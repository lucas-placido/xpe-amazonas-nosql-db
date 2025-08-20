# ==== CONFIG ====
$container = "mongo-primary"           # troque pelo nome do container Mongo (veja com: docker ps)
$db = "amazonas"
$user = "admin"
$pwd = "admin123"
$authDb = "admin"
$limit = 200

# URI (note o uso de ${} para proteger as variáveis dentro da string)
$uri = "mongodb://${user}:${pwd}@localhost:27017/${db}?authSource=${authDb}&authMechanism=SCRAM-SHA-256"

# 1) Obter lista de coleções
$raw = docker exec $container mongosh $uri --quiet --eval 'JSON.stringify(db.getCollectionNames())'
$collections = $raw | ConvertFrom-Json

if (-not $collections) {
    throw "Não foi possível obter as coleções. Confira o container/URI/credenciais."
}

# 2) Exportar cada coleção
foreach ($c in $collections) {
    if ($c -match '^system\.') { continue }

    Write-Host "Exportando $c..."

    # exporta NDJSON dentro do container
    docker exec $container mongoexport --uri "$uri" --collection "$c" --out "/tmp/$c.ndjson" --limit $limit

    # copia para a pasta atual do host
    docker cp "${container}:/tmp/$c.ndjson" ".\$c.ndjson"

    # remove do container
    docker exec $container sh -c "rm -f /tmp/$c.ndjson"
}

Write-Host "✅ Concluído. Arquivos .ndjson gerados na pasta atual."
