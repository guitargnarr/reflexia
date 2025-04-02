#!/usr/bin/env python3
"""
Reflexia Model Manager - Feature Demo Script
This script demonstrates the key features of Reflexia Model Manager
"""
import os
import time
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# Import Reflexia components
from config import Config
from model_manager import ModelManager
from memory_manager import MemoryManager
from prompt_manager import PromptManager
from rag_manager import RAGManager

console = Console()

def print_header():
    """Print a fancy header"""
    console.print(Panel.fit(
        Text("Reflexia Model Manager", style="bold blue"),
        subtitle="Feature Demo",
        border_style="blue"
    ))

def demonstrate_adaptive_quantization(model_manager, memory_manager):
    """Demonstrate adaptive quantization feature"""
    console.print(Panel.fit(
        Text("Adaptive Quantization Demo", style="bold green"),
        border_style="green"
    ))
    
    console.print("Reflexia can dynamically adjust model quantization based on:")
    console.print("  • Content complexity")
    console.print("  • Available system resources")
    console.print("  • Memory pressure\n")
    
    prompts = [
        ("Simple Prompt", "What is the capital of France?"),
        ("Medium Prompt", "Explain the difference between supervised and unsupervised learning in machine learning."),
        ("Complex Prompt", "Can you analyze the structure and potential optimizations for this quantum computing algorithm: H|0⟩ → CNOT(0,1) → H|1⟩ → Rz(θ)|0⟩?")
    ]
    
    for complexity, prompt in prompts:
        console.print(f"[bold]Testing {complexity}[/bold]")
        console.print(f"Prompt: {prompt}")
        
        # Estimate complexity
        content_complexity = model_manager.estimate_content_complexity(prompt)
        console.print(f"Estimated complexity: {content_complexity:.2f}")
        
        # Get initial quantization
        initial_quant = model_manager.quantization
        console.print(f"Initial quantization: [bold]{initial_quant}[/bold]")
        
        # Adapt quantization based on complexity
        changed = model_manager.adaptive_quantization(
            memory_manager=memory_manager, 
            content_complexity=content_complexity
        )
        
        new_quant = model_manager.quantization
        if changed:
            console.print(f"Adapted quantization to: [bold green]{new_quant}[/bold green]")
        else:
            console.print(f"Quantization unchanged: [bold]{new_quant}[/bold]")
        
        # Generate response with timing
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"Generating response with {new_quant} quantization...", total=None)
            
            start_time = time.time()
            response = model_manager.generate_response(prompt=prompt, max_tokens=100)
            elapsed = time.time() - start_time
            
            progress.update(task, completed=True, total=1)
        
        console.print(f"[dim]Response generated in {elapsed:.2f} seconds[/dim]")
        console.print(Panel(response[:200] + ("..." if len(response) > 200 else ""), 
                     border_style="dim"))
        console.print("")
        
        # Wait briefly to let system stabilize 
        time.sleep(2)

def demonstrate_rag(rag_manager):
    """Demonstrate RAG capabilities"""
    if not rag_manager or not rag_manager.is_available():
        console.print("[bold red]RAG not available.[/bold red] Please install ChromaDB and sentence-transformers.")
        return
        
    console.print(Panel.fit(
        Text("Retrieval-Augmented Generation (RAG) Demo", style="bold magenta"),
        border_style="magenta"
    ))
    
    console.print("Reflexia enhances responses with information from your documents.")
    console.print("Let's see how RAG works with sample data.\n")
    
    # Get documents count
    docs = rag_manager.list_documents()
    console.print(f"Found [bold]{len(docs)}[/bold] documents in the knowledge base.")
    
    if len(docs) == 0:
        console.print("[yellow]No documents found. Loading sample data...[/yellow]")
        
        # Create a temporary sample document
        sample_path = "temp_sample.txt"
        with open(sample_path, "w") as f:
            f.write("""
            Reflexia Model Manager is a sophisticated system for deploying, managing, 
            and optimizing large language models with adaptive resource management.
            
            Key features include adaptive quantization, which dynamically adjusts model
            precision based on content complexity and available resources. It also features
            robust memory management, RAG integration, and a web UI.
            
            The system was built in 2025 and is maintained by a team of AI enthusiasts.
            """)
        
        # Load the sample document
        with Progress(console=console) as progress:
            task = progress.add_task("Loading sample document...", total=None)
            success = rag_manager.load_file(sample_path)
            progress.update(task, completed=True, total=1)
        
        if success:
            console.print("[green]Sample document loaded successfully.[/green]")
        else:
            console.print("[red]Failed to load sample document.[/red]")
            return
            
        # Clean up
        if os.path.exists(sample_path):
            os.remove(sample_path)
    
    # Generate a RAG response
    test_query = "When was the Reflexia Model Manager built and what are its key features?"
    
    console.print(f"\n[bold]Test Query:[/bold] {test_query}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Generating RAG response...", total=None)
        
        start_time = time.time()
        result = rag_manager.generate_rag_response(
            test_query,
            system_prompt="You are a helpful AI assistant."
        )
        elapsed = time.time() - start_time
        
        progress.update(task, completed=True, total=1)
    
    console.print(f"[dim]Response generated in {elapsed:.2f} seconds[/dim]")
    
    if "response" in result:
        console.print("\n[bold]RAG Response:[/bold]")
        console.print(Panel(result["response"], border_style="magenta"))
    
    if "sources" in result and result["sources"]:
        console.print("\n[bold]Sources used:[/bold]")
        for src in result["sources"]:
            console.print(f"- {src}")

def demonstrate_memory_management(memory_manager):
    """Demonstrate memory management capabilities"""
    console.print(Panel.fit(
        Text("Memory Management Demo", style="bold cyan"),
        border_style="cyan"
    ))
    
    console.print("Reflexia monitors and manages system memory to ensure stable operation.")
    
    # Get current memory stats
    memory_stats = memory_manager.get_memory_stats()
    
    console.print("\n[bold]Current Memory Stats:[/bold]")
    console.print(f"Total Memory: {memory_stats['total'] / (1024 * 1024 * 1024):.2f} GB")
    console.print(f"Used Memory: {memory_stats['used'] / (1024 * 1024 * 1024):.2f} GB")
    console.print(f"Usage Percentage: {memory_stats['percent']:.1f}%")
    
    # Memory pressure simulation
    console.print("\nSimulating memory pressure response...")
    
    thresholds = [
        (50, "Normal operation - using highest quality model"),
        (70, "Medium memory pressure - recommend reducing model quality"),
        (85, "High memory pressure - emergency model downgrade required"),
        (95, "Critical memory pressure - potential system instability")
    ]
    
    for threshold, description in thresholds:
        status = memory_manager.check_memory_status(threshold_percent=threshold)
        color = "green" if status == "normal" else "yellow" if status == "warning" else "red"
        console.print(f"At {threshold}% usage: [bold {color}]{status}[/bold {color}] - {description}")

def main():
    """Run the feature demonstration"""
    parser = argparse.ArgumentParser(description="Reflexia Model Manager Feature Demo")
    parser.add_argument("--quantization", action="store_true", help="Demo adaptive quantization")
    parser.add_argument("--rag", action="store_true", help="Demo RAG capabilities")
    parser.add_argument("--memory", action="store_true", help="Demo memory management")
    parser.add_argument("--all", action="store_true", help="Demo all features")
    args = parser.parse_args()
    
    # Default to all if no args specified
    if not any([args.quantization, args.rag, args.memory, args.all]):
        args.all = True
    
    print_header()
    
    with Progress(console=console) as progress:
        task = progress.add_task("Initializing Reflexia Model Manager...", total=None)
        
        # Initialize configuration
        config = Config()
        
        # Initialize managers
        model_manager = ModelManager(config)
        memory_manager = MemoryManager(config, model_manager)
        prompt_manager = PromptManager(config)
        
        # Initialize RAG if available
        rag_manager = None
        try:
            import chromadb
            import sentence_transformers
            rag_manager = RAGManager(config, model_manager)
        except ImportError:
            pass
        
        progress.update(task, completed=True, total=1)
    
    console.print("[green]Initialization complete![/green]\n")
    
    # Run demos based on arguments
    if args.all or args.memory:
        demonstrate_memory_management(memory_manager)
        console.print("")
    
    if args.all or args.quantization:
        demonstrate_adaptive_quantization(model_manager, memory_manager)
        console.print("")
    
    if args.all or args.rag:
        demonstrate_rag(rag_manager)
        console.print("")
    
    console.print(Panel.fit(
        Text("Demo Complete", style="bold blue"),
        border_style="blue"
    ))

if __name__ == "__main__":
    main()