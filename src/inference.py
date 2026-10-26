
import argparse
import csv
import json
import time
import os
from pathlib import Path
from datetime import datetime

import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)
DEFAULT_MODEL = "ministral-3:8b-instruct-2512-q4_K_M"


def generate_response(model, prompt, temperature, max_tokens):
    """Envía un prompt a Ollama y calcula métricas de generación."""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        }
    }

    start_time = time.perf_counter()

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=600
    )
    response.raise_for_status()

    data = response.json()
    total_time = time.perf_counter() - start_time

    generated_tokens = data.get("eval_count", 0)
    eval_duration = data.get("eval_duration", 0)
    prompt_eval_duration = data.get("prompt_eval_duration", 0)

    tokens_per_second = (
        generated_tokens / (eval_duration / 1_000_000_000)
        if eval_duration > 0 else 0
    )

    # Estimación del tiempo hasta el primer token (TTFT).
    # Ollama no entrega este dato directamente en modo no streaming.
    # Se estima usando el tiempo de evaluación del prompt.
    ttft_estimated = prompt_eval_duration / 1_000_000_000

    return {
        "output": data.get("response", ""),
        "generated_tokens": generated_tokens,
        "total_time_seconds": round(total_time, 4),
        "tokens_per_second": round(tokens_per_second, 2),
        "ttft_estimated_seconds": round(ttft_estimated, 4)
    }


def load_prompt_file(prompt_file):
    """Lee un archivo de texto usando UTF-8."""

    path = Path(prompt_file)

    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {prompt_file}"
        )

    return path.read_text(encoding="utf-8-sig")


def save_results(results, output_dir):
    """Guarda los resultados en archivos JSON y CSV."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)



   
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = output_dir / f"resultados_{timestamp}.json"
    csv_path = output_dir / f"resultados_{timestamp}.csv"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)

    if results:
        with csv_path.open(
            "w", newline="", encoding="utf-8-sig"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=list(results[0].keys())
            )
            writer.writeheader()
            writer.writerows(results)

    print("\n===== ARCHIVOS GUARDADOS =====")
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")


def run_suite(suite_file, model, temperature, max_tokens, output_dir):
    """Ejecuta todos los prompts definidos en suite.json."""

    path = Path(suite_file)

    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró la suite: {suite_file}"
        )

    with path.open("r", encoding="utf-8-sig") as file:
        suite = json.load(file)

    prompts = suite.get("prompts", [])

    if not prompts:
        raise ValueError(
            "La suite no contiene prompts en la propiedad 'prompts'."
        )

    results = []

    print(f"Modelo: {model}")
    print(f"Cantidad de prompts: {len(prompts)}")
    print(f"Temperatura: {temperature}")
    print("\nIniciando pruebas...\n")

    for index, item in enumerate(prompts, start=1):
        prompt_id = item.get("id", f"P{index:02d}")
        prompt_text = item.get("prompt", "")

        print(f"[{index}/{len(prompts)}] Ejecutando {prompt_id}...")

        try:
            metrics = generate_response(
                model=model,
                prompt=prompt_text,
                temperature=temperature,
                max_tokens=max_tokens
            )

            result = {
                "id": prompt_id,
                "category": item.get("category", ""),
                "task": item.get("task", ""),
                "prompt": prompt_text,
                "output": metrics["output"],
                "generated_tokens": metrics["generated_tokens"],
                "total_time_seconds": metrics["total_time_seconds"],
                "tokens_per_second": metrics["tokens_per_second"],
                "ttft_estimated_seconds": metrics["ttft_estimated_seconds"],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "status": "ejecutado",
                "error": ""
            }

            print(
                f"  Correcto: {metrics['generated_tokens']} tokens, "
                f"{metrics['total_time_seconds']} s"
            )

        except requests.exceptions.RequestException as error:
            result = {
                "id": prompt_id,
                "category": item.get("category", ""),
                "task": item.get("task", ""),
                "prompt": prompt_text,
                "output": "",
                "generated_tokens": 0,
                "total_time_seconds": 0,
                "tokens_per_second": 0,
                "ttft_estimated_seconds": 0,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "status": "error",
                "error": str(error)
            }

            print(f"  Error al consultar Ollama: {error}")

        results.append(result)

    save_results(results, output_dir)

    successful = sum(
        1 for result in results if result["status"] == "ejecutado"
    )
    print(f"\nPruebas completadas: {successful}/{len(results)}")


def main():
    parser = argparse.ArgumentParser(
        description="Inferencia local con Ollama y Ministral"
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Nombre del modelo de Ollama"
    )
    parser.add_argument(
        "--prompt",
        help="Prompt escrito directamente en la terminal"
    )
    parser.add_argument(
        "--prompt-file",
        help="Archivo de texto que contiene un prompt"
    )
    parser.add_argument(
        "--suite",
        help="Archivo JSON con una suite de prompts para ejecutar"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperatura de generación (por defecto: 0.7)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=256,
        help="Máximo de tokens generados"
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Carpeta donde se guardan los resultados"
    )

    args = parser.parse_args()

    if not 0 <= args.temperature <= 2:
        parser.error("--temperature debe estar entre 0 y 2.")

    if args.max_tokens < 1:
        parser.error("--max-tokens debe ser mayor que cero.")

    try:
        if args.suite:
            run_suite(
                suite_file=args.suite,
                model=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                output_dir=args.output_dir
            )

        elif args.prompt_file or args.prompt:
            if args.prompt_file:
                prompt = load_prompt_file(args.prompt_file)
            else:
                prompt = args.prompt

            result = generate_response(
                model=args.model,
                prompt=prompt,
                temperature=args.temperature,
                max_tokens=args.max_tokens
            )

            print("\n===== RESULTADO =====")
            print(result["output"])
            print("\n===== MÉTRICAS =====")
            print(f"Tokens generados: {result['generated_tokens']}")
            print(f"Tiempo total: {result['total_time_seconds']} segundos")
            print(f"Tokens por segundo: {result['tokens_per_second']}")
            print(
                "TTFT estimado (evaluación del prompt): "
                f"{result['ttft_estimated_seconds']} segundos"
            )

        else:
            parser.error(
                "Debe proporcionar --prompt, --prompt-file o --suite."
            )

    except requests.exceptions.ConnectionError:
        print(
            "\nERROR: No se pudo conectar con Ollama. "
            "Verifique que Ollama esté ejecutándose."
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(f"\nERROR: {error}")
    except requests.exceptions.RequestException as error:
        print(f"\nERROR de comunicación con Ollama: {error}")


if __name__ == "__main__":
    main()
