# Utiliza uma imagem oficial e leve de Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do contentor
WORKDIR /app

# Instala dependências essenciais do sistema se necessário
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências do requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código restante da aplicação para o contentor
COPY . .

# Expõe a porta que o Fly.io espera utilizar
EXPOSE 8080

# Comando para iniciar a aplicação com Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]