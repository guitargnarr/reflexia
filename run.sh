#!/bin/bash
# Run script for Reflexia Model Manager

# Check if a command was provided
if [ $# -eq 0 ]; then
    echo "Usage: ./run.sh [command]"
    echo "Available commands:"
    echo "  interactive - Start interactive mode"
    echo "  web - Start web UI"
    echo "  rag - Start interactive mode with RAG"
    echo "  benchmark - Run benchmark tests"
    echo "  examples - Run examples"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Process commands
case $1 in
    interactive)
        python main.py --interactive
        ;;
    web)
        python main.py --web
        ;;
    rag)
        python main.py --interactive --rag
        ;;
    benchmark)
        python main.py --benchmark
        ;;
    examples)
        echo "Running basic inference example..."
        python examples/basic_inference.py
        echo ""
        echo "Running adaptive quantization example..."
        python examples/adaptive_quantization.py
        ;;
    *)
        echo "Unknown command: $1"
        echo "Available commands: interactive, web, rag, benchmark, examples"
        exit 1
        ;;
esac