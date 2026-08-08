import ollama
def get_response(prompt):
    # Create a client to interact with the Ollama API
    response = ollama.chat(model="llama3.2", 
                           messages=[{"role": "user", 
                                      "content": prompt
                                      }
                                      ]  
                                        )

    # Send the prompt to the Ollama API and get the response
    return response["message"]
    ["content"]