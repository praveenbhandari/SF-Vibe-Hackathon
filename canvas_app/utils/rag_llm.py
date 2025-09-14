import os
from typing import List, Dict, Any


def answer_with_context(prompt: str, contexts: List[Dict[str, Any]]) -> str:
    """
    Simple RAG LLM function that uses Ollama for context-aware responses.
    This is a simplified version for the learning mode.
    """
    try:
        import ollama
        
        # Prepare context
        context_text = "\n\n".join([ctx.get("text", "") for ctx in contexts])
        
        # Create the full prompt with context
        full_prompt = f"""Context from course materials:
{context_text}

Question: {prompt}

Please provide a helpful response based on the context above."""
        
        # Use Ollama for response
        model_name = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "user", "content": full_prompt}
            ],
            options={
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 500
            }
        )
        
        return response.get("message", {}).get("content", "I'm sorry, I couldn't generate a response.")
        
    except Exception as e:
        return f"I'm sorry, I encountered an error while processing your request: {str(e)}"
