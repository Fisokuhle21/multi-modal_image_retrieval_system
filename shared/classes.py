from dataclasses import dataclass
from enum import Enum, unique
import PIL.JpegImagePlugin
from transformers import CLIPProcessor, CLIPModel, \
    CLIPTokenizer, BlipProcessor, BlipForConditionalGeneration, \
    BertTokenizer, AutoProcessor, BarkModel
import pandas as pd
import numpy as np
import chromadb

@unique
class Modalities(Enum):
    """A class containing available modality conversions"""
    ti = "text_to_image"
    it = "image_to_text"
    vt = "voice_to_text"
    tv = "text_to_voice"

    @staticmethod
    def get_modality_config(modality) -> dict:
        """Get the config for a given modality"""
        config = None

        if modality == Modalities.ti:
            config = {
                "model_name": CLIPModel,
                "processor_name": CLIPProcessor,
                "tokenizer_name": CLIPTokenizer
            }
        elif modality == Modalities.it:
            config = {
                "model_name": BlipForConditionalGeneration,
                "processor_name": BlipProcessor,
                "tokenizer_name": BertTokenizer
            }
        elif modality == Modalities.tv:
            config = {
                "model_name": BarkModel,
                "processor_name": AutoProcessor,
                "tokenizer_name": None
            }

        return config


@dataclass
class Model:
    """A class containing a standard model setup"""
    dataframe: pd.DataFrame = None
    model_id:str = None
    device:str = "cpu"
    model: CLIPModel = None
    processor: CLIPProcessor = None
    tokenizer: CLIPTokenizer = None

    def get_model_info(self, modality) -> tuple:
        """Get the information needed for a model, suct as the model, processor, and tokenizer"""
        # Get the model, processor & tokenizer to use
        modality_config = Modalities.get_modality_config(modality)

        # Save the model to device
        self.model = modality_config["model_name"].from_pretrained(self.model_id).to(self.device)
        # Get the processor
        self.processor = modality_config["processor_name"].from_pretrained(self.model_id)
        # Get the tokenizer
        self.tokenizer = modality_config["tokenizer_name"].from_pretrained(self.model_id) if modality_config["tokenizer_name"] is not None else None
        # Return model, processor & tokenizer
        return self.model, self.processor, self.tokenizer

    def get_single_text_embedding(self, query: str) -> np.ndarray:
        """Create text embeddings and convert them to a numpy array""" 
        inputs = self.tokenizer(query, return_tensors = "pt")
        text_embeddings = self.model.get_text_features(**inputs)
        # convert the embeddings to numpy array
        embedding_as_np = text_embeddings.cpu().detach().numpy()
        return embedding_as_np

    def get_single_image_embedding(self, the_image: PIL.JpegImagePlugin.JpegImageFile) -> np.ndarray:
        """Create image embeddings and convert them to a numpy array""" 
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
    """A class containing methods used to interect with Chromadb"""
    collection_name: str = None
    collection: chromadb.Collection = None
    client: chromadb.PersistentClient = chromadb.PersistentClient(path="db/")

    def create_collection(self, db_metadata: dict) -> chromadb.Collection:
        """Create a Chromadb collection"""
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata=db_metadata
        )
        return self.collection
    
    def get_collection(self) -> chromadb.Collection:
        """Get an existing collection"""
        self.collection = self.client.get_collection(name=self.collection_name)
        return self.collection

    def add_data(self, dataframe: pd.DataFrame) -> None:
        """Add or update existing data in Chromadb collection"""
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