from fasthtml.common import *
from monsterui.all import *
from dotenv import load_dotenv
from openai import AsyncOpenAI
import os


load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise RuntimeError("Coloque OPENROUTER_API_KEY no .env")

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY
)

app, rt = fast_app(hdrs=Theme.blue.headers())

async def make_completion(system_prompt: str, user_prompt: str,
                          model="tngtech/deepseek-r1t2-chimera:free"):
    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return resp.choices[0].message.content.strip()

@rt('/')
def index():

    return Titled(
        "Gerador de Textos para vídeos",
        Card(
            
            P("Preencha o tema do vídeo para gerar automaticamente título, descrição e tags.",
              cls=TextPresets.muted_sm),

            Form(
                LabelInput("Tema do vídeo", name="tema", type="text",
                           placeholder="ex: Como aprender Python", required=True),
                DivCentered(
                    Button("Gerar", type="submit", cls=ButtonT.primary)
                ),
                hx_post="/processar",
                hx_target="#saida",
                hx_indicator="#loading"
                
            ),
            DivCentered(
                # O componente Loading cria a animação (tente: infinity, spinner, dots, ring)
                Loading(cls=LoadingT.infinity, htmx_indicator=True),
                Span(" Criando conteúdo...", cls="ml-3 text-muted"),
                id="loading",
                cls="htmx-indicator mt-6" 
            ),
            Div(id="saida",cls="mt-4")
        
        )
    )

@rt("/processar", methods=["POST"])
async def processar(tema: str):

    system_title = """Você é um assistente prestativo e educado,
                Você recebe um tema para título de vídeo do Youtube e gera apenas uma sugestão de título.
                Não diga nada além da sugestão."""
    user_title = f"Crie um título atraente para um vídeo do YouTube sobre: {tema}"
    titulo = await make_completion(system_prompt=system_title, user_prompt=user_title)
    titulo = titulo.strip('"')
    system_desc = (
        "Gere uma descrição de YouTube otimizada para SEO. "
        "Não inclua hashtags. Não adicione texto extra."
    )
    user_desc = f"Sugira uma descrição para o vídeo com o tema:{tema} e título: {titulo}"
    descricao = await make_completion(system_prompt=system_desc, user_prompt=user_desc)
    
    system_tags = """Você é um assistente prestativo e educado,
                Você recebe um tema e um título e descrição de vídeo do Youtube e retorna as hashtags
                com foco em SEO. Retorne as hashtags separadas por vírgula e sem o símbolo de jogo da velha na frente. Não diga nada além das hashtags.
    """
    user_tags = f"Gere as palavras-chave para o vídeo de tema:{tema}, título: {titulo} e descrição:{descricao}"
    tags = await make_completion(system_prompt=system_tags, user_prompt=user_tags)
    return Card(
        H3("Título:"),
        LabelInput("Título", value=titulo, readonly=True),
        H3("Descrição:"),
        TextArea(descricao, readonly=True, rows=10),
        H3("Tags:"),
        LabelInput("Tags", value=tags, readonly=True),
    )


serve()