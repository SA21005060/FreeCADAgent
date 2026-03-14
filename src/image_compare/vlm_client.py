from langchain_google_genai import ChatGoogleGenerativeAI
from src.load_environment import load_env
from langchain.schema import HumanMessage
from pathlib import Path

from src.llm_service import get_llm

GEMINI_API_KEY = load_env.GEMINI_API_KEY_IMAGE
image_path_cad = Path("generated/screenshot.png") # Update image paths
image_path_downloaded = r"C:\Users\yasin\Desktop\flange_downloaded.jpeg" # Update image paths

# llm = ChatGoogleGenerativeAI(
#     model="gemma-3-12b-it",
#     api_key=GEMINI_API_KEY
# )
llm = get_llm()

messages = [
       HumanMessage(
        content=(
            "You are an expert CAD engineer working with FreeCAD 1.0.1. You are given two images:"
            "The first image is a CAD-generated geometry described as: user_input." # Use {user_input} linked to the actual user input for llm
            "The second image is a real part that the CAD geometry needs to replicate."
            "Your task: Compare the CAD geometry (image 1) with the real part (image 2) and identify **all major design changes required to make the CAD model match the real part."

            "Requirements:"
            "Think like a CAD engineer modifying a FreeCAD model."
            "Focus only on features of the image, geometry, structural features, structure, overall structure."
            "Ignore color, texture, or surface finish. Dont write about differences in general apperance, color, texture, or surface finish"
            "Output **clear, step-by-step, pointwise instructions** describing exactly what changes to make in the CAD geometry. give only instructions, dont give any prefix like let's analyze the images and outline the necessary CAD modifications in FreeCAD"
            "Be precise with positions, and features whenever possible. make maximum of 7 lines"
            
        ),
        # additional_kwargs={"images": [image_path_cad]}  # Pass both images
        additional_kwargs={"images": [image_path_cad, image_path_downloaded]}  # Pass both images

        # additional_kwargs={"images": [cad_bytes, real_bytes]}
    )
]

response = llm.invoke(messages)
print(response.content)