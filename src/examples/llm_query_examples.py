# src/examples/llm_query_examples.py
"""Examples of using the LLM integration for natural language queries."""

import asyncio
import os
from dotenv import load_dotenv

from src.reportportal_ai.llm.providers.openai_provider import OpenAIProvider
from src.reportportal_ai.llm.providers.anthropic_provider import AnthropicProvider
from src.reportportal_ai.llm.providers.ollama_provider import OllamaProvider
from src.reportportal_ai.rag.rag_pipeline import RAGPipeline
from src.reportportal_ai.core.logging import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging("INFO", "console")


async def example_basic_query():
    """Example: Basic natural language query."""
    print("=== Basic Query Example ===\n")
    
    # Initialize OpenAI provider
    llm = OpenAIProvider()
    
    # Initialize RAG pipeline
    rag = RAGPipeline(llm)
    
    # Ask a question
    question = "What tests failed in the last 24 hours?"
    
    result = await rag.query(question)
    
    print(f"Question: {question}")
    print(f"\nAnswer: {result['response']}")
    print(f"\nIntent detected: {result['analysis']['intent']}")
    print(f"Entity types searched: {result['analysis']['entity_types']}")


async def example_metrics_query():
    """Example: Query asking for metrics and statistics."""
    print("\n=== Metrics Query Example ===\n")
    
    llm = OpenAIProvider()
    rag = RAGPipeline(llm)
    
    question = "What's the failure rate for API tests this week?"
    
    result = await rag.query(question, n_results=50)
    
    print(f"Question: {question}")
    print(f"\nAnswer: {result['response']}")
    
    if result.get('metrics'):
        print("\nCalculated Metrics:")
        print(f"  Failure rate: {result['metrics'].get('failure_rate', 'N/A'):.1f}%")
        print(f"  Success rate: {result['metrics'].get('success_rate', 'N/A'):.1f}%")
        print(f"  Total items analyzed: {result['metrics']['total_items']}")


async def example_root_cause_analysis():
    """Example: Root cause analysis query."""
    print("\n=== Root Cause Analysis Example ===\n")
    
    llm = OpenAIProvider()
    rag = RAGPipeline(llm)
    
    question = "Why are the login tests failing? What's the root cause?"
    
    result = await rag.query(question, n_results=30)
    
    print(f"Question: {question}")
    print(f"\nAnswer: {result['response']}")


async def example_streaming_response():
    """Example: Streaming response for better UX."""
    print("\n=== Streaming Response Example ===\n")
    
    llm = OpenAIProvider()
    rag = RAGPipeline(llm)
    
    question = "Analyze the test failure trends over the last 7 days"
    
    result = await rag.query(question, stream=True)
    
    print(f"Question: {question}")
    print("\nAnswer: ", end="", flush=True)
    
    async for chunk in result['response']:
        print(chunk, end="", flush=True)
    
    print("\n")


async def example_with_sources():
    """Example: Query with source documents included."""
    print("\n=== Query with Sources Example ===\n")
    
    llm = OpenAIProvider()
    rag = RAGPipeline(llm)
    
    question = "Find all timeout errors in the checkout tests"
    
    result = await rag.query(
        question,
        n_results=10,
        include_raw_results=True
    )
    
    print(f"Question: {question}")
    print(f"\nAnswer: {result['response']}")
    
    if result.get('search_results'):
        print(f"\nFound {len(result['search_results'])} relevant documents:")
        for i, doc in enumerate(result['search_results'][:3], 1):
            print(f"\n{i}. {doc['metadata']['entity_type']}")
            print(f"   Distance: {doc['distance']:.4f}")
            print(f"   Preview: {doc['document'][:100]}...")


async def example_comparative_analysis():
    """Example: Comparative analysis query."""
    print("\n=== Comparative Analysis Example ===\n")
    
    llm = OpenAIProvider()
    rag = RAGPipeline(llm)
    
    question = "Compare the test results between this week and last week. What changed?"
    
    result = await rag.query(question, n_results=50)
    
    print(f"Question: {question}")
    print(f"\nAnswer: {result['response']}")


async def example_with_feedback():
    """Example: Refining a query with feedback."""
    print("\n=== Query with Feedback Example ===\n")
    
    llm = OpenAIProvider()
    rag = RAGPipeline(llm)
    
    # Initial query
    question = "What tests are failing?"
    result = await rag.query(question)
    
    print(f"Initial Question: {question}")
    print(f"Initial Answer: {result['response']}")
    
    # Refine with feedback
    feedback = "I need more specific information about the error messages and which test suites are affected"
    
    refined_result = await rag.query_with_feedback(
        query=question,
        previous_response=result['response'],
        feedback=feedback
    )
    
    print(f"\nFeedback: {feedback}")
    print(f"Refined Answer: {refined_result['response']}")


async def example_ollama_local():
    """Example: Using Ollama for local LLM inference."""
    print("\n=== Ollama Local LLM Example ===\n")
    
    try:
        # Initialize Ollama provider
        async with OllamaProvider(
            base_url="http://localhost:11434",
            model="llama2"
        ) as llm:
            rag = RAGPipeline(llm)
            
            question = "Summarize the test failures from today"
            
            result = await rag.query(question)
            
            print(f"Question: {question}")
            print(f"\nAnswer (from local LLM): {result['response']}")
            
    except Exception as e:
        print(f"Ollama error: {e}")
        print("Make sure Ollama is running: ollama serve")


async def example_multi_turn_conversation():
    """Example: Multi-turn conversation with context."""
    print("\n=== Multi-turn Conversation Example ===\n")
    
    llm = OpenAIProvider()
    rag = RAGPipeline(llm)
    
    # Conversation flow
    conversations = [
        "What's the overall test status for the API module?",
        "Which specific endpoints are failing?",
        "What are the common error patterns in these failures?"
    ]
    
    context = []
    
    for question in conversations:
        print(f"\nUser: {question}")
        
        # For follow-up questions, we could maintain context
        # This is a simplified example
        result = await rag.query(question)
        
        print(f"Assistant: {result['response']}")
        
        # Store for context (in a real implementation)
        context.append({
            "question": question,
            "response": result['response']
        })


async def main():
    """Run all examples."""
    try:
        # Check if required environment variables are set
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
            print("Error: Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file")
            print("\nExample .env file:")
            print("OPENAI_API_KEY=your-key-here")
            print("# or")
            print("ANTHROPIC_API_KEY=your-key-here")
            return
        
        # Make sure data is synced first
        print("Note: Make sure you have synced data using:")
        print("  poetry run reportportal_ai sync run --project YOUR_PROJECT\n")
        
        # Run examples
        await example_basic_query()
        await example_metrics_query()
        await example_root_cause_analysis()
        await example_streaming_response()
        await example_with_sources()
        await example_comparative_analysis()
        await example_with_feedback()
        
        # Optional: Run Ollama example if available
        # await example_ollama_local()
        
        await example_multi_turn_conversation()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())