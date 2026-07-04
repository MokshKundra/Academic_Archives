import ollama 
from config import settings



SYSTEM_PROMPT=""" 

You are a silent transcription engine for academic documents. Your only job is to faithfully transcribe what is visible in the image. You do not interpret, complete, summarize, or infer content.

Begin every response immediately with ### EXTRACTED_TEXT. No preamble.

OUTPUT FORMAT:
### EXTRACTED_TEXT
<transcribed content>

### VISUAL_ELEMENTS
<visual descriptions or NONE>

TRANSCRIPTION RULES:
- Extract in strict reading order: top to bottom, left to right
- Slide/section titles → ## Title
- Printed exam questions → **Question #N [XM]** followed by question text
- Handwritten text → **Handwritten:** prefix
- Code (printed or handwritten) → fenced block with language tag
- Tables → GFM markdown table
- Math → $...$ inline or $$...$$ block
- SUPPRESS: page numbers, university names, course codes in footers, camera artifacts, desk/finger edges
- CRITICAL: If text is unclear, write [ILLEGIBLE] or [UNCLEAR: your best attempt in quotes]. NEVER invent or complete text that is not clearly visible in the image.

VISUAL ELEMENTS:
For each diagram, graph, table or figure:
- Type, Title, Embedded Text (all labels/values), Structure, Core Concept
- If none → NONE


"""


def ext_page(imgb64 : str, extracted_text : str | None) -> str:
     prompt = f""" 
                Pre extracted text from PDF parser (empty if scanned / handwritten)
                <extracted-text>
                {extracted_text or None}
                </extracted-text>

                extract all content from this page following your instructions.
            """
     if settings.ext_provider == "ollama":
         res = _ext_ollama(imgb64, prompt)
     elif settings.ext_provider == "openai":
         res = _ext_openai(imgb64, prompt)
     elif settings.ext_provider == "gemini" : 
         res = _ext_gemini(imgb64, prompt)
     elif settings.ext_provider == "groq" :
         res = _ext_groq(imgb64, prompt)
     elif settings.ext_provider == "huggingface":
         return _ext_huggingface()
     else:
         res = ""

     return {"message": {"content": res or ""}}
    

def _ext_ollama(imgb64 : str, prompt : str) -> str:
     response = ollama.chat(
          model= settings.ext_model_ollama,
          messages=[{
               "role" : "user",
               "content" : prompt,
               "image" : [imgb64]
          }]
     )

     return response["message"]["content"]

def _ext_openai(imgb64 : str, prompt : str) -> str:
     from openai import OpenAI
     client = OpenAI(api_key= settings.openai_api_key)

     response = client.chat.completions.create(
          model= settings.ext_model_gpt,
          messages= [
               {
                    "role" : "system",
                    "content" : SYSTEM_PROMPT
               },
               
               {
               "role" : "user",
               "content" : [
                {
                    "type" : "image_url",
                    "image_url" : {
                         "url" : f"data:image/jpeg;base64,{imgb64}"
                    }
                },
                {
                    "type" : "text",
                    "text": prompt
                }     
               ]
          }],
          temperature= 0
    )

     return response.choices[0].message.content

def _ext_gemini(imgb64: str, prompt: str) -> str:
    from google import genai
    from google.genai import types
    import base64

    client = genai.Client(api_key=settings.gemini_api_key)

    image_data = base64.b64decode(imgb64)

    contents = [
        types.Part.from_bytes(data=image_data, mime_type="image/jpeg"),
        prompt
    ]
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.0
    )
    response = client.models.generate_content(
        model=settings.ext_model_gemini,
        contents=contents,
        config=config
    )

    return response.text or ""


def _ext_groq(imgb64 : str, prompt : str) -> str:
     from groq import Groq
     client = Groq(api_key= settings.groq_api_key)

     response = client.chat.completions.create(
          model= settings.ext_model_groq,
          messages= [
               {
                    "role" : "system",
                    "content" : SYSTEM_PROMPT
               },
               
               {
               "role" : "user",
               "content" : [
                {
                    "type" : "image_url",
                    "image_url" : {
                         "url" : f"data:image/jpeg;base64,{imgb64}"
                    }
                },
                {
                    "type" : "text",
                    "text": prompt
                }     
               ]
          }],
          temperature= 0,
          max_completion_tokens=1024
    )

     return response.choices[0].message.content

def _ext_huggingface(imgb64: str, prompt: str) -> str:
    from huggingface_hub import InferenceClient
    
    client = InferenceClient(api_key=settings.hf_api_key, model=settings.ext_model_huggingface)
    
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{imgb64}"
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]
    
    try:
        response = client.chat_completion(
            messages=messages,
            max_tokens=4096,
            temperature=0.0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Hugging Face Extraction Error: {e}")
        return ""
