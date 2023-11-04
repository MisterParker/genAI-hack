class Chatbot:
    def __init__(self, vectorstore_index):
        self.vectorstore_index = vectorstore_index
        self.memory = {}
        self.chat_log = []
        self.context = []

    def query_vectorstore(self, query):
        query_answer = self.vectorstore_index.query_with_sources(query)
        answer = query_answer['answer']
        sources = query_answer['sources']
        sources_str = str(sources)
        print(query_answer)
        return answer, sources_str
    
    def reset_context(self):
        self.context = []
        self.memory = {}
    
    def ask(self, question):
        if question.lower() == "reset":
            self.reset_context()
            return "Context has been reset.", "SMRT Chatbot"
        
        if question in self.memory:
            response, source = self.memory[question]

        else:
            answer, source = self.query_vectorstore(question)

            if answer:
                self.memory[question] = answer, source
                response = answer
            else:
                response = "I don't know the answer to that question."

        self.chat_log.append({'user_input': question, 'response': response, 'source': source})
        print(self.chat_log[-1])
        return response, source

