from dataclasses import dataclass
import PIL.BmpImagePlugin
import PIL.JpegImagePlugin
from transformers import CLIPProcessor, CLIPModel, \
    CLIPTokenizer, BlipProcessor, BlipForConditionalGeneration, \
    BertTokenizer, AutoProcessor, BarkModel
import pandas as pd
import numpy as np
import chromadb
import PIL


@dataclass
class Model:
    dataframe: pd.DataFrame = None
    model_id:str = None
    device:str = "cpu"
    model: CLIPModel = None
    processor: CLIPProcessor = None
    tokenizer: CLIPTokenizer = None

    def get_model_info(self, modality: str) -> tuple:

        modalities = {
            "ti": {
                "model_name": CLIPModel,
                "processor_name": CLIPProcessor,
                "tokenizer_name": CLIPTokenizer
            },
            "it": {
                "model_name": BlipForConditionalGeneration,
                "processor_name": BlipProcessor,
                "tokenizer_name": BertTokenizer
            },
            "tv": {
                "model_name": BarkModel,
                "processor_name": AutoProcessor,
                "tokenizer_name": None
            }
        }

        model_name, processor_name, tokenizer_name = modalities[modality]

        # Save the model to device
        self.model = model_name.from_pretrained(self.model_id).to(self.device)
        # Get the processor
        self.processor = processor_name.from_pretrained(self.model_id)
        # Get the tokenizer
        self.tokenizer = tokenizer_name.from_pretrained(self.model_id) if tokenizer_name is not None else None
        # Return model, processor & tokenizer
        return self.model, self.processor, self.tokenizer

    def get_single_text_embedding(self, query: str) -> np.ndarray: 
        inputs = self.tokenizer(query, return_tensors = "pt")
        text_embeddings = self.model.get_text_features(**inputs)
        # convert the embeddings to numpy array
        embedding_as_np = text_embeddings.cpu().detach().numpy()
        return embedding_as_np

    def get_single_image_embedding(self, the_image: PIL.JpegImagePlugin.JpegImageFile) -> np.ndarray:
        image = self.processor(
                text = None,
                images = the_image,
                return_tensors="pt"
                )["pixel_values"].to(self.device)
        embedding = self.model.get_image_features(image)
        # convert the embeddings to numpy array
        embedding_as_np = embedding.cpu().detach().numpy()
        return embedding_as_np


@dataclass
class Chroma:
    collection_name: str = None
    collection: chromadb.Collection = None
    client: chromadb.PersistentClient = chromadb.PersistentClient(path="db/")

    def create_collection(self, db_metadata: dict) -> chromadb.Collection:
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata=db_metadata
        )
        return self.collection
    
    def get_collection(self) -> chromadb.Collection:
        self.collection = self.client.get_collection(name=self.collection_name)
        return self.collection

    def add_data(self, dataframe: pd.DataFrame) -> None:
        dataframe["vector_id"] = dataframe.index
        dataframe["vector_id"] = dataframe["vector_id"].apply(str)
        dataframe["img_embeddings"] = sum(dataframe["img_embeddings"].apply(lambda x: x.tolist() if isinstance(x, np.ndarray) else x), [])
        # Get all the metadata
        final_metadata = []
        for index in range(len(dataframe)):
            final_metadata.append({
                'ID':  index,
                'caption': dataframe.iloc[index].filename,
                'image': dataframe.iloc[index].filepath
            })
        image_IDs = dataframe.vector_id.tolist()
        image_embeddings = [img_embeddings for img_embeddings in dataframe["img_embeddings"]]
        
        self.collection.upsert(
        ids=image_IDs,
        embeddings=image_embeddings,
        metadatas=final_metadata
        )