# Open WebUI with OpenAI API and RAG

Complete Docker setup for Open WebUI using OpenAI API for chat completions and RAG (Retrieval-Augmented Generation) with PDF document support.

## Features

- **OpenAI Integration**: Use GPT-4o, GPT-4 Turbo, or any OpenAI chat model
- **RAG/Document Q&A**: Upload PDFs, create knowledge bases, and chat with your documents
- **Persistent Storage**: All data survives container restarts (chats, uploads, embeddings)
- **No Local LLMs**: Uses only OpenAI API (no Ollama, no local model runtime)
- **Built-in Vector Database**: Open WebUI includes ChromaDB for embeddings

## Prerequisites

1. **Docker & Docker Compose**
   - Docker Desktop (macOS/Windows) or Docker Engine (Linux)
   - Docker Compose v3.8+
   - Verify: `docker --version` and `docker compose version`

2. **OpenAI API Key**
   - Sign up at https://platform.openai.com/
   - Create API key at https://platform.openai.com/api-keys
   - Ensure you have credits/billing enabled

3. **System Requirements**
   - Minimum: 2 GB RAM, 5 GB disk space
   - Recommended: 4 GB RAM for processing large PDFs

## Quick Start

### 1. Initial Setup

```bash
# Clone or navigate to this directory
cd /path/to/rag

# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

**Important**: Replace `OPENAI_API_KEY=sk-proj-xxx...` with your actual API key.

### 2. Start Open WebUI

```bash
# Start the container
docker compose up -d

# Check logs
docker compose logs -f open-webui

# Wait for "Application startup complete" message
```

### 3. Access the UI

Open your browser: **http://localhost:3000**

**First-time setup:**
1. Create an admin account (first user becomes admin)
2. You'll be redirected to the main chat interface

### 4. Stop/Restart

```bash
# Stop
docker compose down

# Restart
docker compose restart

# Stop and remove volumes (DELETES ALL DATA)
docker compose down -v
```

## OpenAI Configuration

### Setting up OpenAI API

Open WebUI should automatically detect your OpenAI API key from environment variables. To verify:

1. **Navigate to Settings**:
   - Click your avatar (bottom left)
   - Select **Settings**

2. **Connections → OpenAI**:
   - Verify **API Key** shows as configured (masked)
   - Confirm **API Base URL**: `https://api.openai.com/v1`
   - Test connection if available

### Selecting an OpenAI Model

**In the Chat Interface:**

1. Click the **model selector** at the top of the chat
2. You should see available OpenAI models:
   - `gpt-4o` (recommended, default)
   - `gpt-4-turbo`
   - `gpt-3.5-turbo`
   - Other models you have access to

3. Select your preferred model
4. Start chatting!

**Troubleshooting model list:**
- If no models appear, check Settings → Connections → OpenAI
- Verify your API key has access to the models
- Check Docker logs for API errors: `docker compose logs open-webui`

## RAG / Document Q&A Setup

Open WebUI includes built-in RAG capabilities with vector search powered by ChromaDB.

### Enabling Documents Feature

1. **Navigate to Workspace → Documents** (or **Knowledge**)
   - Click the menu icon (top left)
   - Select **Workspace** → **Documents** or **Knowledge**

2. **First Time Setup**:
   - The Documents/Knowledge feature should be enabled by default
   - If prompted, confirm to enable document processing

### Uploading PDFs

**Method 1: Upload to Knowledge Base**

1. Go to **Workspace → Documents**
2. Click **+ Add Document** or **Upload**
3. Select one or more PDF files
4. Wait for processing (parsing + embedding generation)
5. Once complete, the document appears in your library

**Method 2: Upload During Chat**

1. Start a new chat
2. Click the **📎 (paperclip)** or **+** icon in the message input
3. Select **Upload Files** or **Add Document**
4. Choose PDF file(s)
5. The document will be processed and attached to the current chat

### Configuring Embeddings (OpenAI)

Open WebUI uses OpenAI's embedding models for RAG:

1. **Settings → Documents**:
   - Click avatar → **Settings**
   - Navigate to **Documents** or **RAG** section

2. **Embedding Model Configuration**:
   - **Embedding Engine**: Select **OpenAI**
   - **Embedding Model**: Choose `text-embedding-3-small` (default, recommended)
     - Alternatives: `text-embedding-3-large`, `text-embedding-ada-002`
   - **API Key**: Should inherit from OPENAI_API_KEY environment variable

3. **Save changes**

**Note**: Embeddings are generated once per document and stored in the persistent volume (`open-webui-data`). Re-uploading the same document will regenerate embeddings.

### Using RAG in Chats

**Option A: Attach Documents to Chat**

1. Start a new chat
2. Click the **document icon** or **#** next to the message input
3. Select documents from your library
4. Type your question and send
5. Open WebUI retrieves relevant chunks and includes them in the context

**Option B: Create a Collection**

1. **Workspace → Documents**
2. Create a **Collection** (group of related documents)
3. Add multiple PDFs to the collection
4. In chat, select the collection instead of individual documents

**Option C: Query Mode**

1. Some Open WebUI versions have a **"Search Documents"** or **"RAG Mode"** toggle
2. Enable it to automatically search your knowledge base with every query

### RAG Settings

**Settings → Documents**:

- **Chunk Size**: Size of text chunks for embedding (default: 400-1500)
- **Chunk Overlap**: Overlap between chunks (default: 200)
- **Top K**: Number of relevant chunks to retrieve (default: 5)
- **Relevance Threshold**: Minimum similarity score (optional)

**Best Practices:**
- Use smaller chunk sizes (400-800) for precise Q&A
- Use larger chunk sizes (1000-1500) for summarization
- Increase Top K (10-20) for complex questions spanning multiple topics

## Persistence and Data Storage

### Where Data is Stored

All data is stored in the Docker volume: **`open-webui-data`**

**Includes:**
- User accounts and authentication
- Chat history and conversations
- Uploaded documents (PDFs, files)
- Vector embeddings (ChromaDB database)
- Model configurations and settings

**Volume Location:**

```bash
# Inspect volume
docker volume inspect open-webui-data

# Location (varies by OS):
# macOS: /var/lib/docker/volumes/open-webui-data/_data
# Linux: /var/lib/docker/volumes/open-webui-data/_data
```

### Backup and Restore

**Backup:**

```bash
# Stop the container
docker compose down

# Create backup
docker run --rm \
  -v open-webui-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/open-webui-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restart
docker compose up -d
```

**Restore:**

```bash
# Stop container
docker compose down

# Remove old volume
docker volume rm open-webui-data

# Create new volume
docker volume create open-webui-data

# Restore data
docker run --rm \
  -v open-webui-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/open-webui-backup-YYYYMMDD.tar.gz -C /data

# Start
docker compose up -d
```

## Security Notes

### API Key Protection

- **NEVER commit `.env` to version control** (it's gitignored)
- Rotate your OpenAI API key periodically
- Monitor usage at https://platform.openai.com/usage
- Set spending limits in OpenAI dashboard

### Network Exposure

**Default Configuration (Secure):**
- Bound to `127.0.0.1:3000` (localhost only)
- Only accessible from your local machine

**External Access (Use with Caution):**

Edit `docker-compose.yml`:

```yaml
ports:
  - "0.0.0.0:3000:8080"  # Accessible from any network interface
```

**Recommendations for External Access:**
- Use a reverse proxy (nginx, Traefik) with HTTPS
- Enable authentication: Set `ENABLE_SIGNUP=false` after creating admin account
- Use a firewall to restrict access
- Consider VPN or SSH tunnel for remote access

### User Management

**Disable Public Signup:**

Add to `docker-compose.yml` environment:

```yaml
- ENABLE_SIGNUP=false
```

Then create user accounts via admin panel only.

## Troubleshooting

### Container won't start

**Check logs:**

```bash
docker compose logs -f open-webui
```

**Common issues:**
- Port 3000 already in use: Change port in `docker-compose.yml`
- Volume permission errors: Reset volume with `docker compose down -v` (deletes data!)

### "OpenAI API Key not configured"

**Fix:**

1. Verify `.env` file exists and contains `OPENAI_API_KEY=sk-...`
2. Restart container: `docker compose restart`
3. Check environment variables inside container:
   ```bash
   docker compose exec open-webui env | grep OPENAI
   ```

### No OpenAI models appear

**Possible causes:**

1. **Invalid API key**:
   - Test key manually: `curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"`
   - Check OpenAI dashboard for key status

2. **API key lacks permissions**:
   - Ensure billing is enabled
   - Verify key has access to chat models

3. **Network issues**:
   - Check container logs for API errors
   - Verify Docker has internet access

### Documents not processing / RAG not working

**Diagnosis:**

1. **Check embedding configuration**:
   - Settings → Documents → Ensure OpenAI embedding model is selected
   - Verify `OPENAI_API_KEY` is configured

2. **Check document upload logs**:
   ```bash
   docker compose logs -f open-webui | grep -i "embed\|document\|rag"
   ```

3. **Verify volume persistence**:
   ```bash
   docker volume inspect open-webui-data
   ```

4. **Re-upload document**:
   - Delete document from knowledge base
   - Upload again (will regenerate embeddings)

**Common errors:**

- `Embedding model not configured`: Set embedding model in Settings → Documents
- `OpenAI API quota exceeded`: Check usage limits at platform.openai.com
- `Document processing failed`: Check PDF is not corrupted, try a smaller file first

### Large PDF fails to process

**Solutions:**

1. **Increase container memory**: Add to `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 4G
   ```

2. **Split large PDFs** into smaller files (< 100 pages each)

3. **Check logs** for specific errors:
   ```bash
   docker compose logs open-webui | grep -i error
   ```

### Embeddings not persisting after restart

**Verify volume is mounted:**

```bash
docker compose down
docker compose up -d
docker compose exec open-webui ls -la /app/backend/data
```

**Expected output**: Should show `vector_db` or `chroma` directory

**Fix**: Ensure `volumes:` section in `docker-compose.yml` is correct.

### Reset everything (nuclear option)

```bash
# Stop and remove all data
docker compose down -v

# Remove images (optional)
docker rmi ghcr.io/open-webui/open-webui:main

# Start fresh
docker compose up -d
```

## Updating Open WebUI

**Check for updates:**

```bash
# Pull latest image
docker compose pull

# Recreate container with new image
docker compose up -d
```

**Pinning to a specific version:**

Edit `docker-compose.yml`:

```yaml
image: ghcr.io/open-webui/open-webui:v0.1.124  # Replace with desired version
```

Check releases: https://github.com/open-webui/open-webui/releases

## Advanced Configuration

### Custom OpenAI API Base URL

For proxies or API gateways, edit `.env`:

```bash
OPENAI_API_BASE_URL=https://your-proxy.example.com/v1
```

### Environment Variables Reference

See `docker-compose.yml` and `.env.example` for all available options.

**Key variables:**
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `OPENAI_API_BASE_URL` - API endpoint (default: https://api.openai.com/v1)
- `OPENAI_API_MODEL` - Default chat model (default: gpt-4o)
- `ENABLE_OLLAMA_API` - Disable Ollama (set to false)
- `ENABLE_OPENAI_API` - Enable OpenAI (set to true)

## Resources

- **Open WebUI Docs**: https://docs.openwebui.com/
- **Open WebUI GitHub**: https://github.com/open-webui/open-webui
- **OpenAI API Docs**: https://platform.openai.com/docs/
- **OpenAI Models**: https://platform.openai.com/docs/models
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings

## License

Open WebUI is licensed under the MIT License.
This configuration is provided as-is for educational and development purposes.
# openweb_rag
