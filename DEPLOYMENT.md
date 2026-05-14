# Production Deployment Guide

## Pre-Deployment Checklist

- [ ] All environment variables configured in `.env`
- [ ] `OPENAI_API_KEY` is set and valid
- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] No localhost-only configurations
- [ ] Logging is configured and working
- [ ] Error handling is comprehensive
- [ ] Database directory exists and is writable

## Environment Setup for Production

### 1. Set Required Environment Variables

```bash
export OPENAI_API_KEY=sk-your-production-key
export OPENAI_MODEL=gpt-4o
export AGENT_MAX_ITERATIONS=10
export AGENT_MAX_TOKENS=3000
export SIMILARITY_THRESHOLD=0.6
export CHUNK_SIZE=1000
export CHUNK_OVERLAP=200
export CHROMA_PATH=/var/lib/autonomous_research/chroma_db
```

### 2. Create Data Directory

```bash
mkdir -p /var/lib/autonomous_research/chroma_db
chmod 755 /var/lib/autonomous_research
chmod 755 /var/lib/autonomous_research/chroma_db
```

### 3. Deploy with Streamlit

#### Option A: Direct Streamlit Deployment

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

#### Option B: Using Gunicorn (Recommended for Production)

```bash
pip install gunicorn
gunicorn -w 1 -b 0.0.0.0:8000 "streamlit.cli:main" -- run app.py
```

#### Option C: Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

Build and run:

```bash
docker build -t autonomous-research-agent .
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=sk-your-key \
  -v /data/chroma_db:/app/data/chroma_db \
  autonomous-research-agent
```

### 4. Configure Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Enable HTTPS (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Security Considerations

1. **API Keys**: Use environment variables, never hardcode keys
2. **Rate Limiting**: Implement rate limiting on the proxy
3. **Authentication**: Add authentication layer (Basic Auth, OAuth2)
4. **HTTPS**: Always use HTTPS in production
5. **Input Validation**: Validate all user inputs
6. **Logging**: Monitor and log all requests
7. **Resource Limits**: Set CPU and memory limits
8. **Regular Updates**: Keep dependencies up to date

## Monitoring & Logging

### Application Logging

Logs are output to stdout by default. Configure in `app.py`:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/autonomous_research/app.log'),
        logging.StreamHandler()
    ]
)
```

### System Monitoring

Monitor these metrics:

- API response times
- Vector DB size and query performance
- Error rates
- Token usage and costs
- Memory usage

### Example Monitoring Setup (with Prometheus)

```python
from prometheus_client import start_http_server, Counter, Histogram
import time

# Metrics
requests_total = Counter('requests_total', 'Total requests')
response_time = Histogram('response_seconds', 'Response time')

@response_time.time()
def handle_request():
    requests_total.inc()
    # Process request
    pass

# Start metrics server on port 8000
start_http_server(8000)
```

## Cost Management

### API Usage Optimization

1. **Use GPT-4o-mini**: Reduce costs by 20x
2. **Limit iterations**: Set `AGENT_MAX_ITERATIONS=5`
3. **Batch requests**: Process multiple documents together
4. **Cache results**: Implement caching for repeated queries

### Cost Monitoring

Track daily/monthly costs:

```python
from datetime import date
import json

COST_LOG = "/var/log/autonomous_research/costs.jsonl"

def log_token_usage(tokens_used, model):
    cost = tokens_used * pricing[model]
    with open(COST_LOG, 'a') as f:
        f.write(json.dumps({
            'date': str(date.today()),
            'model': model,
            'tokens': tokens_used,
            'cost': cost
        }) + '\n')
```

## Scaling Considerations

### Horizontal Scaling

For multiple instances, use:

- Shared ChromaDB (hosted or network mount)
- Redis for session management
- Load balancer (Nginx, HAProxy)

### Database Optimization

```bash
# Regular maintenance
chroma:> VACUUM
chroma:> OPTIMIZE
```

### Performance Tuning

```env
# Increase for faster responses
AGENT_MAX_TOKENS=5000

# Decrease for lower latency
CHUNK_SIZE=500

# Increase for better recall
SIMILARITY_THRESHOLD=0.5
```

## Backup & Disaster Recovery

### Regular Backups

```bash
#!/bin/bash
BACKUP_DIR="/backups/autonomous_research"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup ChromaDB
tar -czf $BACKUP_DIR/chroma_db_$TIMESTAMP.tar.gz /var/lib/autonomous_research/chroma_db

# Keep only last 30 days
find $BACKUP_DIR -name "chroma_db_*.tar.gz" -mtime +30 -delete
```

### Recovery Procedure

```bash
# Extract backup
tar -xzf $BACKUP_DIR/chroma_db_latest.tar.gz -C /var/lib/autonomous_research/

# Verify integrity
python -c "import chromadb; c = chromadb.PersistentClient('/var/lib/autonomous_research/chroma_db'); print(f'Collections: {len(c.list_collections())}')"
```

## Troubleshooting Production Issues

### High Memory Usage

```bash
# Check memory
ps aux | grep streamlit

# Reduce CHUNK_SIZE or AGENT_MAX_TOKENS
```

### Slow API Responses

1. Check OpenAI API status
2. Reduce `AGENT_MAX_ITERATIONS`
3. Scale horizontally with load balancer

### Database Errors

```bash
# Check ChromaDB integrity
python -c "
import chromadb
client = chromadb.PersistentClient('/path/to/chroma_db')
for col in client.list_collections():
    print(f'{col.name}: {col.count()} items')
"
```

## Support & Maintenance

- Monitor logs daily
- Update dependencies monthly
- Test new API models quarterly
- Review costs weekly
- Backup data daily
