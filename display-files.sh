#!/bin/bash

display_files() {
    local dir="$1"
    
    for file in "$dir"/*; do
        if [ -d "$file" ]; then
            display_files "$file"  # Рекурсивный вызов для директорий
        elif [ -f "$file" ]; then
            echo "--- File: $file ---"
            cat "$file"
            echo "" # Пустая строка для разделения файлов
        fi
    done
}

display_files "${1:-.}"
