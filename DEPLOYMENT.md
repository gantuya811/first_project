# MERRIGE ERP — Production Deployment Runbook

Энэ баримт бичиг нь MERRIGE ERP-ийг бодит (production) серверт анх удаа
байршуулах, өдөр тутам ажиллуулах, болон гэмтэл засварлах (troubleshoot)
алхмуудыг тайлбарлана.

> **Тайлбар:** STEP18-ийн доорх заавруудыг энэ хөгжүүлэлтийн машин дээр
> Docker суулгагдаагүй тул бодит контейнер орчинд ажиллуулж шалгах
> боломжгүй байсан (STEP17-тай ижил хязгаарлалт). Файлуудын синтакс
> (YAML, shell) статик байдлаар шалгагдсан бөгөөд бүтэц/логик нь
> Docker/Compose/nginx/certbot-ийн албан ёсны баримт бичигт нийцүүлэн
> бичигдсэн. Бодит серверт анх байршуулахдаа энэ баримт бичгийн
> алхмуудыг дараалан, болгоомжтой дагана уу.

## 1. Урьдчилсан шаардлага (Prerequisites)

- Ubuntu 22.04+ (эсвэл ижил төстэй Linux) сервер, `sudo` эрхтэй хэрэглэгч
- Docker Engine 24+ болон Docker Compose plugin (`docker compose version`)
- Домэйн нэр (жишээ: `merrige.mn`), DNS A-бичлэг серверийн IP рүү заасан байх
- 80, 443 портууд нээлттэй (firewall)
- Git суулгасан, репозиторийг clone хийх эрхтэй

## 2. Анхны тохиргоо (Initial Setup)

```bash
git clone <repository-url> /opt/merrige
cd /opt/merrige

cp .env.example .env
# .env файлыг нээж дараах утгуудыг заавал бодит утгаар солино:
#   SECRET_KEY, ALLOWED_HOSTS, DB_PASSWORD, DB_NAME, DB_USER,
#   EMAIL_HOST_USER/PASSWORD, SITE_DOMAIN
# DJANGO_SETTINGS_MODULE-г production болгож солино:
#   DJANGO_SETTINGS_MODULE=config.settings.production
```

`ALLOWED_HOSTS`-д бодит домэйн нэрээ заавал нэмнэ (жишээ:
`ALLOWED_HOSTS=merrige.mn,www.merrige.mn`).

### 2.1. SSL-гүйгээр эхлээд шалгах (заавал биш, зөвлөмж)

Домэйн/DNS бэлэн болохоос өмнө HTTP-аар л түр ажиллуулж стек бүрэн
эхэлж байгааг шалгаж болно:

```bash
docker compose up -d --build
docker compose ps
curl -f http://<server-ip>/health/
```

## 3. SSL сертификат анх удаа авах (Let's Encrypt)

```bash
export SITE_DOMAIN_NAME=merrige.mn
export CERTBOT_EMAIL=admin@merrige.mn
./scripts/init_certbot.sh
```

Энэ скрипт дараах алхмуудыг дараалан хийнэ:
1. `docker/nginx/templates/default.conf.template`-г `envsubst`-ээр
   `docker/nginx/merrige.ssl.conf` болгон домэйн нэрийг орлуулж үүсгэнэ.
2. HTTP-only nginx-ийг эхлүүлж, ACME challenge (`/.well-known/...`) замыг
   нээнэ.
3. `certbot/certbot` image-ийг ашиглан `docker/certbot/conf`-т
   сертификат авна.
4. `docker-compose.yml` + `docker-compose.prod.yml`-г хамт ашиглан
   HTTPS-тэй бүтэн стекийг эхлүүлнэ.

Амжилттай бол:

```bash
curl -f https://merrige.mn/health/
```

Сертификат нь `docker-compose.prod.yml` доторх `certbot` service-ээр
12 цаг тутам автоматаар шинэчлэгдэнэ (renew) — нэмэлт cron шаардлагагүй.

## 4. Superuser (Admin) үүсгэх

```bash
docker compose exec web python manage.py createsuperuser
```

Утасны дугаар (phone_number), имэйл, нууц үг оруулна (Монгол хэлний
нууц үгийн шаардлага: доод тал нь 8 тэмдэгт, том/жижиг үсэг, тоо).

## 5. Өдөр тутмын ажиллагаа

### 5.1. Байршуулалт шинэчлэх (deploy)

```bash
./scripts/deploy.sh
```

Энэ скрипт: `git pull` → Docker image дахин build → контейнер шинэчлэх
(migration/collectstatic нь `docker/entrypoint.sh`-ээр автоматаар
ажиллана) → хуучин image цэвэрлэх дарааллаар ажиллана. SSL идэвхжсэн бол
(`docker/nginx/merrige.ssl.conf` байгаа бол) автоматаар
`docker-compose.prod.yml`-г мөн хамт ашиглана.

### 5.2. Өгөгдлийн сан нөөцлөлт (backup)

```bash
./scripts/backup_db.sh
```

Cron-д тохируулах жишээ (`crontab -e`):

```cron
0 3 * * * cd /opt/merrige && BACKUP_RETENTION_DAYS=14 ./scripts/backup_db.sh >> logs/backup.log 2>&1
```

Нөөц файлууд `./backups/` дотор `.sql.gz` хэлбэрээр хадгалагдаж,
`BACKUP_RETENTION_DAYS`-аас хуучирсан файлууд автоматаар устгагдана
(анхдагч 14 хоног).

### 5.3. Сэргээх (restore) — гэмтэл засварын үед ашиглана

```bash
gunzip -c backups/merrige_merrige_erp_20260101_030000.sql.gz | \
    docker compose exec -T db psql -U merrige_user -d merrige_erp
```

## 6. CI/CD (`.github/workflows/ci.yml`)

- **`test` job** (`main`-руу push/PR бүрт ажиллана): `flake8` lint шалгаад,
  `pytest --cov=apps --cov-fail-under=80`-ээр тест ажиллуулна. SQLite +
  LocMemCache ашигладаг `config.settings.test` тохиргоог ашигладаг тул
  CI дотор Postgres/Redis service шаардлагагүй.
- **`build` job** (зөвхөн `main`-д push хийгдэх үед, `test` job амжилттай
  дууссаны дараа): Docker image-ийг барьж, `ghcr.io/<repo>:latest` болон
  `ghcr.io/<repo>:<commit-sha>` tag-аар GitHub Container Registry-д
  push хийнэ.

Серверт бодит deploy хийхийг CI автоматаар хийхгүй (аюулгүй байдлын
үүднээс) — `./scripts/deploy.sh`-г серверт гараар (эсвэл cron/webhook-оор)
ажиллуулна.

## 7. Гэмтэл засварлах (Troubleshooting)

| Асуудал | Шалгах алхам |
|---|---|
| `/health/` 503 буцаана | `docker compose logs web`, `docker compose logs db` — DB/Redis холболт шалгах |
| Migration ажиллахгүй | `docker compose logs web` — `docker/entrypoint.sh`-ийн DB хүлээх лог шалгах (30 удаа, 2 сек тутам) |
| SSL сертификат авахад алдаа гарсан | Домэйны DNS A-бичлэг зөв эсэх, 80-р порт нээлттэй эсэхийг шалгах; `docker compose logs nginx` |
| Static файл (CSS/зураг) харагдахгүй байна | `docker compose exec web python manage.py collectstatic --noinput`-г дахин ажиллуулах, nginx `/static/` alias зам шалгах |
| Celery ажил гүйцэтгэхгүй байна | `docker compose logs celery_worker`, Redis холболт (`REDIS_URL`) шалгах |
| Нэвтрэхэд "хэт олон оролдлого" алдаа гарна | Rate limiting (throttle) хэвийн ажиллаж байгааг илтгэнэ — жинхэнэ хэрэглэгч бол хэдэн минут хүлээх |

## 8. Аюулгүй байдлын сануулга

- `.env` файлыг **хэзээ ч** git-д commit хийхгүй (`.gitignore`-д орсон)
- `docker/certbot/conf/` (сертификат/түлхүүр) болон `docker/nginx/merrige.ssl.conf`
  (домэйн-с хамааралтай) мөн git-д ороогүй — серверт локал үүсдэг
- `SECRET_KEY`-г production-д давхардаагүй, санамсаргүй урт утгаар солих
- DB нөөцийг сервертэй ижил байршилд бус, тусдаа (offsite) хадгалахыг зөвлөнө
