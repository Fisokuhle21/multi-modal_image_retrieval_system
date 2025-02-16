from PIL import Image
from shared.classes import Model as md, Modalities as mo, Chroma as ch
from pydub import AudioSegment
from io import BytesIO
from datetime import datetime
import pandas as pd
import chromadb
import whisper

ti_model = md(model_id="openai/clip-vit-base-patch32")

def get_all_images_embedding(df: pd.DataFrame, img_column:pd.DataFrame.columns) -> pd.DataFrame:
    """Create embeddings for a provided image"""
    ti_model.get_model_info(modality=mo.ti)
    df["img_embeddings"] = df[str(img_column)].apply(ti_model.get_single_image_embedding)
    return df

def get_results(query: str, collection: chromadb.Collection) -> dict:
    """Query the Chroma vector store"""
    query_vect = ti_model.get_single_text_embedding(query)
    res = collection.query(
        query_embeddings=query_vect,
        n_results=3
        )
    
    return res

def run_text_to_image(query: str, create_collection: bool=False, add_data: bool=False) -> dict:
    """Run the process to retrieve images based on the a user query"""
    df = pd.read_csv("images/image.csv")
    df.drop(columns=["Unnamed: 0"], inplace=True)
    df["image"] = df["filepath"].apply(lambda x: Image.open(x))

    image_data_df = get_all_images_embedding(df, "image")

    chroma = ch(collection_name="my_collection")

    if create_collection:
        collection = chroma.create_collection(db_metadata={
                "description": "my first Chroma collection",
                "created": str(datetime.now()),
                "hnsw:space": "cosine",
            })
    else:
        collection = chroma.get_collection()

    if add_data:
        chroma.add_data(image_data_df)

    res = get_results(query, collection)

    return res

def generate_captions(top_images: dict) -> list:
    """Generate captions for given images"""
    it_model = md(model_id="Salesforce/blip-image-captioning-base")
    model, processor, _ = it_model.get_model_info(modality=mo.it)
    image_links = [img['image'] for img in top_images["metadatas"][0]]
    list_images = [Image.open(image_link) for image_link in image_links]
    captions = []
    for img in list_images:
        inputs = processor(img, return_tensors="pt")
        output = model.generate(**inputs)
        # decode the generated caption
        caption = processor.decode(output[0], skip_special_tokens=True)
        captions.append(caption)
    return captions

def generate_audio_from_text(response) -> tuple:
    """Generate audio from a provided text input"""
    tv_model = md(model_id="suno/bark")
    model, processor, _ = tv_model.get_model_info(modality=mo.tv)
    voice_preset = "v2/en_speaker_6"
    inputs = processor(response, voice_preset=voice_preset)
    audio_array = model.generate(**inputs)
    audio_array = audio_array.cpu().numpy().squeeze()
    sample_rate = model.generation_config.sample_rate
    return audio_array, sample_rate

def save_file_as_mp3(uploaded_file, output_path, bitrate="192k") -> str:
    """Save a provided audio file as an mp3 file"""
    audio = AudioSegment.from_file(BytesIO(uploaded_file.read()), format="wav")
    audio.export(output_path, format="mp3", bitrate=bitrate)
    return output_path

def convert_audio_to_text(audio) -> str:
    """Convert an input audio file to text"""
    model = whisper.load_model("base")
    data = save_file_as_mp3(audio, "audio/audio.mp3")
    result = model.transcribe(data)
    return result["text"]