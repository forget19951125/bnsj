module.exports = {
  apps: [{
    name: 'bnsj-server',
    script: '/opt/bnsj/bn_auto/server/venv/bin/python',
    args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000',
    cwd: '/opt/bnsj/bn_auto/server',
    interpreter: 'none',
    instances: 1,
    exec_mode: 'fork',
    env: {
      MYSQL_DATABASE: 'bnsj',
      MYSQL_PASSWORD: 'bnsj123456',
      MYSQL_HOST: 'localhost',
      MYSQL_PORT: '3306',
      MYSQL_USER: 'bnsj',
      REDIS_HOST: 'localhost',
      REDIS_PORT: '6379',
      REDIS_PASSWORD: '',
      REDIS_DB: '0',
      JWT_SECRET: 'bn-auto-secret-key-2024',
      ADMIN_TOKEN: 'admin-secret-token',
      HOST: '0.0.0.0',
      PORT: '8000',
      DEBUG: 'False'
    },
    error_file: '/opt/bnsj/logs/pm2-error.log',
    out_file: '/opt/bnsj/logs/pm2-out.log',
    log_file: '/opt/bnsj/logs/pm2-combined.log',
    time: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    min_uptime: '10s',
    max_restarts: 10
  }]
};

