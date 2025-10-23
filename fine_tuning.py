#!/usr/bin/env python3
"""
fine_tuning.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.
"""

Fine-tuning Manager for Reflexia LLM implementation
Handles LoRA fine-tuning and model customization
"""

import os
import logging
import json
import subprocess
import tempfile
from pathlib import Path
import time
import shutil

logger = logging.getLogger("reflexia-tools.finetune")

class FineTuningManager:
    """Manager for fine-tuning Reflexia models"""
    
    def __init__(self, config):
        """Initialize the fine-tuning manager"""
        self.config = config
        
        # Load fine-tuning configuration
        self.ft_method = config.get("fine_tuning", "method", default="lora")
        self.lora_r = config.get("fine_tuning", "lora_r", default=16)
        self.lora_alpha = config.get("fine_tuning", "lora_alpha", default=32)
        self.lora_dropout = config.get("fine_tuning", "lora_dropout", default=0.05)
        self.learning_rate = config.get("fine_tuning", "learning_rate", default=2e-4)
        self.batch_size = config.get("fine_tuning", "batch_size", default=4)
        self.epochs = config.get("fine_tuning", "epochs", default=3)
        
        # Set up directories
        self.models_dir = Path(config.get("paths", "models_dir", default="models"))
        self.datasets_dir = Path(config.get("paths", "datasets_dir", default="datasets"))
        
        # Ensure directories exist
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Fine-tuning manager initialized")
    
    def _prepare_training_data(self, dataset_path, output_file=None):
        """Prepare dataset for Ollama fine-tuning"""
        logger.info(f"Preparing training data from {dataset_path}")
        
        if output_file is None:
            output_file = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.jsonl',
                delete=False
            ).name
        
        try:
            # Check if dataset is a file or directory
            dataset_path = Path(dataset_path)
            
            if dataset_path.is_file():
                # Single file dataset
                if dataset_path.suffix in ['.json', '.jsonl']:
                    self._convert_dataset(dataset_path, output_file)
                else:
                    logger.error(f"Unsupported dataset format: {dataset_path.suffix}")
                    raise ValueError(f"Unsupported dataset format: {dataset_path.suffix}")
            elif dataset_path.is_dir():
                # Directory of files
                self._process_dataset_directory(dataset_path, output_file)
            else:
                logger.error(f"Dataset path does not exist: {dataset_path}")
                raise ValueError(f"Dataset path does not exist: {dataset_path}")
            
            logger.info(f"Training data prepared and saved to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            if os.path.exists(output_file):
                os.unlink(output_file)
            raise
    
    def _convert_dataset(self, input_file, output_file):
        """Convert a dataset file to Ollama format"""
        with open(input_file, 'r') as f_in:
            # Determine file format
            if input_file.suffix == '.json':
                # Assume JSON array
                data = json.load(f_in)
                
                with open(output_file, 'w') as f_out:
                    for item in data:
                        # Extract relevant fields based on common formats
                        prompt = item.get('instruction', item.get('prompt', item.get('input', '')))
                        response = item.get('output', item.get('response', item.get('completion', '')))
                        
                        if prompt and response:
                            example = {"prompt": prompt, "response": response}
                            f_out.write(json.dumps(example) + '\n')
            
            elif input_file.suffix == '.jsonl':
                # JSONL format
                with open(output_file, 'w') as f_out:
                    for line in f_in:
                        if line.strip():
                            item = json.loads(line)
                            prompt = item.get('instruction', item.get('prompt', item.get('input', '')))
                            response = item.get('output', item.get('response', item.get('completion', '')))
                            
                            if prompt and response:
                                example = {"prompt": prompt, "response": response}
                                f_out.write(json.dumps(example) + '\n')
    
    def _process_dataset_directory(self, dir_path, output_file):
        """Process a directory of dataset files"""
        with open(output_file, 'w') as f_out:
            # Process each JSON or JSONL file
            for file_path in dir_path.glob('**/*.json*'):
                try:
                    with open(file_path, 'r') as f_in:
                        # Determine file format
                        if file_path.suffix == '.json':
                            # JSON array
                            data = json.load(f_in)
                            
                            for item in data:
                                prompt = item.get('instruction', item.get('prompt', item.get('input', '')))
                                response = item.get('output', item.get('response', item.get('completion', '')))
                                
                                if prompt and response:
                                    example = {"prompt": prompt, "response": response}
                                    f_out.write(json.dumps(example) + '\n')
                        
                        elif file_path.suffix == '.jsonl':
                            # JSONL format
                            for line in f_in:
                                if line.strip():
                                    item = json.loads(line)
                                    prompt = item.get('instruction', item.get('prompt', item.get('input', '')))
                                    response = item.get('output', item.get('response', item.get('completion', '')))
                                    
                                    if prompt and response:
                                        example = {"prompt": prompt, "response": response}
                                        f_out.write(json.dumps(example) + '\n')
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
    
    def _create_modelfile(self, base_model, training_file, model_name=None):
        """Create an Ollama Modelfile for fine-tuning"""
        logger.info(f"Creating Modelfile for {base_model}")
        
        if model_name is None:
            model_name = f"{base_model}-custom"
        
        # Create Modelfile content
        modelfile_content = f"""

FROM {base_model}
SYSTEM "You are a helpful AI assistant that has been fine-tuned on specialized data."

# Fine-tuning data
TRAIN {os.path.basename(training_file)}
"""
        
        # Create Modelfile
        modelfile_path = os.path.join(self.models_dir, "Modelfile")
        with open(modelfile_path, 'w') as f:
            f.write(modelfile_content)
        
        # Copy training file to models directory
        shutil.copy(training_file, os.path.join(self.models_dir, os.path.basename(training_file)))
        
        logger.info(f"Modelfile created at {modelfile_path}")
        return modelfile_path, model_name
    
    def fine_tune_model(self, dataset_path, model_name=None, base_model=None):
        """Fine-tune a model using Ollama"""
        logger.info(f"Starting fine-tuning process with dataset {dataset_path}")
        
        try:
            # Set base model if not provided
            if base_model is None:
                base_model = self.config.get("model", "name", default="reflexia-r1")
            
            # Set model name if not provided
            if model_name is None:
                model_name = f"{base_model}-custom-{int(time.time())}"
            
            # Prepare training data
            logger.info("Preparing training data...")
            training_file = self._prepare_training_data(dataset_path)
            
            # Create Modelfile
            logger.info("Creating Modelfile...")
            modelfile_path, model_name = self._create_modelfile(base_model, training_file, model_name)
            
            # Change to models directory
            os.chdir(self.models_dir)
            
            # Run Ollama create command
            logger.info(f"Creating custom model {model_name}...")
            result = subprocess.run(
                ["ollama", "create", model_name, "-f", "Modelfile"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Error creating model: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "model_name": model_name
                }
            
            logger.info(f"Model {model_name} created successfully")
            
            # Run a quick test to verify the model
            logger.info("Testing fine-tuned model...")
            test_result = subprocess.run(
                ["ollama", "run", model_name, "Hello, how are you?", "--format", "json"],
                capture_output=True,
                text=True
            )
            
            # Return success
            return {
                "success": True,
                "model_name": model_name,
                "metrics": {
                    "training_examples": self._count_examples(training_file),
                    "creation_time": time.time()
                }
            }
            
        except Exception as e:
            logger.error(f"Error during fine-tuning: {e}")
            return {
                "success": False,
                "error": str(e),
                "model_name": model_name if 'model_name' in locals() else None
            }
        finally:
            # Clean up temporary files
            if 'training_file' in locals() and os.path.exists(training_file):
                os.unlink(training_file)
    
    def _count_examples(self, jsonl_file):
        """Count number of examples in a JSONL file"""
        count = 0
        with open(jsonl_file, 'r') as f:
            for line in f:
                if line.strip():
                    count += 1
        return count
    
    def list_custom_models(self):
        """List all custom models"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Error listing models: {result.stderr}")
                return []
            
            # Parse output to find custom models
            lines = result.stdout.strip().split('\n')
            custom_models = []
            
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    model_name = parts[0]
                    
                    # Check if it's a custom model
                    if "-custom" in model_name:
                        custom_models.append({
                            "name": model_name,
                            "id": parts[1] if len(parts) > 1 else "",
                            "size": parts[2] + " " + parts[3] if len(parts) > 3 else "",
                            "modified": " ".join(parts[4:]) if len(parts) > 4 else ""
                        })
            
            return custom_models
            
        except Exception as e:
            logger.error(f"Error listing custom models: {e}")
            return []