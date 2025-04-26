# llm_qa.py
import os
import streamlit as st
from typing import List, Optional
from vidavox.generation.llm import Client  # or the official openai library, etc.

def answer_with_llm(
    context: str,
    question: str,
    model_name: str = "openai:gpt-3.5-turbo",
    temperature: float = 0.75,
):
    """
    1. Builds a prompt that includes 'context' (transcription or conversation) and 'question' (user or predefined).
    2. Sends request to the chosen LLM (OpenAI, LLaMA, etc.).
    3. Returns the string response.
    """

    # Flexible prompt that instructs the assistant to follow the user’s instructions,
    # leveraging the provided context. 
    system_prompt = (
        "You are a helpful assistant. You carefully follow the user's instructions and use any provided context. "
        "If the context does not contain enough information to fully answer, state so politely. "
        "Be concise and clear in your response."
    )

    # The user message includes the context plus the question.
    user_prompt = f"""
    Context or conversation details:
    {context}

    User Instruction / Question:
    {question}

    Please follow the user's instructions as best as you can, using the above context if relevant.
    If the question cannot be answered from the context, respond accordingly.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        openai_client = Client(model=model_name)
        response = openai_client.chat.completions.create(
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        st.error(f"Error calling LLM: {e}")
        return "LLM request failed."
