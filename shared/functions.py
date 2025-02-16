from PIL import Image
import matplotlib.pyplot as plt
from shared.classes import Model as md
import pandas as pd
import chromadb
from scipy.io.wavfile import write as write_wav
import whisper

ti_model = md(model_id="openai/clip-vit-base-patch32")

def get_all_images_embedding(df: pd.DataFrame, img_column:pd.DataFrame.columns) -> pd.DataFrame:
    ti_model.get_model_info(modality="ti")
    df["img_embeddings"] = df[str(img_column)].apply(ti_model.get_single_image_embedding)
    return df

def get_results(query: str, collection: chromadb.Collection) -> dict:
    query_vect = ti_model.get_single_text_embedding(query)
    res = collection.query(
        query_embeddings=query_vect,
        n_results=4
        )
    
    return res

def plot_images_by_side_(top_images: dict) -> None:
    image_links = [img['image'] for img in top_images["metadatas"][0]]
    list_images = [Image.open(image_link) for image_link in image_links]
    distance = top_images["distances"][0]
    n_row = n_col = 2
    _, axs = plt.subplots(n_row, n_col, figsize=(12, 12))
    axs = axs.flatten()
    for img, ax, sim_score in zip(list_images, axs, distance):
        ax.imshow(img)
        sim_score = 100*float("{:.2f}".format(1-sim_score))
        ax.title.set_text(f"Similarity: {sim_score}%")
    plt.show()

def generate_captions(top_images: dict) -> list:
    it_model = md(model_id="Salesforce/blip-image-captioning-base")
    model, processor, _ = it_model.get_model_info(modality="it")
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

def generate_audio_from_text(response):
    tv_model = md(model_id="suno/bark")
    model, processor, _ = tv_model.get_model_info(modality="tv")
    voice_preset = "v2/en_speaker_6"
    inputs = processor(response, voice_preset=voice_preset)
    audio_array = model.generate(**inputs)
    audio_array = audio_array.cpu().numpy().squeeze()
    sample_rate = model.generation_config.sample_rate
    write_wav("audio/bark_generation.wav", sample_rate, audio_array)

def convert_audio_to_text(audio) -> str:
    model = whisper.load_model("base")
    result = model.transcribe(audio)
    return result["text"]