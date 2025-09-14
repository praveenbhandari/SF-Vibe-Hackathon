import os
import time
from typing import List, Dict, Any


def answer_with_context(prompt: str, contexts: List[Dict[str, Any]]) -> str:
    """
    Simple RAG LLM function that uses Groq API for context-aware responses.
    This is a simplified version for the learning mode.
    """
    try:
        from openai import OpenAI
        
        # Prepare context
        context_text = "\n\n".join([ctx.get("text", "") for ctx in contexts])
        
        # Create the full prompt with context
        full_prompt = f"""Context from course materials:
{context_text}

Question: {prompt}

Please provide a helpful response based on the context above."""
        
        # Use Groq API
        client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        
        model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
        # Retry logic for rate limiting
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500,
                    top_p=0.9
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    # Rate limit hit, wait and retry
                    wait_time = min(2 ** attempt + 1, 10)  # Exponential backoff, max 10 seconds
                    print(f"Rate limit hit, waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
        
        return "I'm sorry, I couldn't generate a response after multiple attempts."
        
    except Exception as e:
        return f"I'm sorry, I encountered an error while processing your request: {str(e)}"
