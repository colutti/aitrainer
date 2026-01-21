
try:
    from langchain.memory import ConversationBufferWindowMemory
    print("Found in langchain.memory")
except ImportError as e:
    print(f"Not in langchain.memory: {e}")

try:
    from langchain_classic.memory import ConversationBufferWindowMemory
    print("Found in langchain_classic.memory")
except ImportError as e:
    print(f"Not in langchain_classic.memory: {e}")
