import os
from pymongo import MongoClient, ASCENDING, TEXT
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:admin123@localhost:27017/?authSource=admin")
DB_NAME = os.getenv("MONGO_DB", "amazonas")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def create_collection_with_schema(name: str, schema: dict):
    """
    Cria a coleção com validador de schema (se não existir) ou atualiza o validador.
    Garante também índices essenciais definidos após a criação.
    """
    # Cria se não existir
    if name not in db.list_collection_names():
        db.create_collection(name)
        print(f"[OK] Coleção criada: {name}")
    else:
        print(f"[INFO] Coleção já existe: {name}")

    # Aplica/atualiza o validador de schema
    db.command({
        "collMod": name,
        "validator": {"$jsonSchema": schema},
        "validationLevel": "moderate"  # valida novos documentos/updates (moderado é mais flexível que strict)
    })
    print(f"[OK] Validador aplicado em: {name}")

def ensure_indexes(name: str, indexes: list[tuple]):
    """
    Cria índices conforme lista de tuplas: (keys, options_dict)
    Exemplo: [(([("email", ASCENDING)], {"unique": True}))]
    """
    col = db[name]
    for keys, options in indexes:
        col.create_index(keys, **options)
    print(f"[OK] Índices garantidos em: {name}")

# ---------------------------
# Schemas de validação (MongoDB JSON Schema)
# ---------------------------

customers_schema = {
  "bsonType": "object",
  "required": ["customer_id", "name", "email", "created_at"],
  "properties": {
    "_id": {},
    "customer_id": {"bsonType": "string", "description": "UUID ou string única"},
    "name": {"bsonType": "string"},
    "email": {"bsonType": "string"},
    "phones": {
      "bsonType": ["array"],
      "items": {"bsonType": "string"}
    },
    "addresses": {
      "bsonType": ["array"],
      "items": {
        "bsonType": "object",
        "required": ["label", "street", "city", "state", "zip", "country"],
        "properties": {
          "label": {"bsonType": "string"},
          "street": {"bsonType": "string"},
          "number": {"bsonType": ["string", "int"]},
          "complement": {"bsonType": ["string", "null"]},
          "district": {"bsonType": "string"},
          "city": {"bsonType": "string"},
          "state": {"bsonType": "string"},
          "zip": {"bsonType": "string"},
          "country": {"bsonType": "string"},
          "is_default": {"bsonType": "bool"}
        }
      }
    },
    "created_at": {"bsonType": "date"},
    "updated_at": {"bsonType": ["date", "null"]}
  }
}

products_schema = {
  "bsonType": "object",
  "required": ["product_id", "title", "price", "category", "created_at"],
  "properties": {
    "_id": {},
    "product_id": {"bsonType": "string", "description": "SKU/ID do produto"},
    "title": {"bsonType": "string"},
    "description": {"bsonType": ["string", "null"]},
    "category": {"bsonType": "string"},
    "brand": {"bsonType": ["string", "null"]},
    "price": {"bsonType": ["double", "decimal", "int"]},
    "currency": {"bsonType": "string"},
    "images": {"bsonType": ["array"], "items": {"bsonType": "string"}},
    "attributes": {"bsonType": "object"},   # flexível: cor, tamanho, material, etc.
    "dimensions": {
      "bsonType": "object",
      "properties": {
        "weight_kg": {"bsonType": ["double", "decimal", "int"]},
        "width_cm": {"bsonType": ["double", "decimal", "int"]},
        "height_cm": {"bsonType": ["double", "decimal", "int"]},
        "depth_cm": {"bsonType": ["double", "decimal", "int"]}
      }
    },
    "stock": {  # estoque geral; para multidepósito, indicamos uma coleção separada no futuro
      "bsonType": "object",
      "properties": {
        "available": {"bsonType": ["int", "long"]},
        "reserved": {"bsonType": ["int", "long"]}
      }
    },
    "status": {"enum": ["ACTIVE", "INACTIVE", "DISCONTINUED"]},
    "created_at": {"bsonType": "date"},
    "updated_at": {"bsonType": ["date", "null"]}
  }
}

carts_schema = {
  "bsonType": "object",
  "required": ["customer_id", "items", "updated_at"],
  "properties": {
    "_id": {},
    "customer_id": {"bsonType": "string"},
    "items": {
      "bsonType": "array",
      "items": {
        "bsonType": "object",
        "required": ["product_id", "title", "unit_price", "qty"],
        "properties": {
          "product_id": {"bsonType": "string"},
          "title": {"bsonType": "string"},          # snapshot do nome
          "unit_price": {"bsonType": ["double", "decimal", "int"]},  # snapshot do preço ao adicionar
          "qty": {"bsonType": ["int", "long"]},
          "variant": {"bsonType": ["object", "null"]}  # ex.: cor/tamanho
        }
      }
    },
    "updated_at": {"bsonType": "date"}
  }
}

orders_schema = {
  "bsonType": "object",
  "required": [
    "order_id", "customer_id", "status", "items",
    "total_amount", "currency", "created_at"
  ],
  "properties": {
    "_id": {},
    "order_id": {"bsonType": "string"},
    "customer_id": {"bsonType": "string"},
    "status": {"enum": ["PLACED", "PAID", "SHIPPED", "DELIVERED", "CANCELLED", "REFUNDED"]},
    "items": {
      "bsonType": "array",
      "items": {
        "bsonType": "object",
        "required": ["product_id", "title", "unit_price", "qty"],
        "properties": {
          "product_id": {"bsonType": "string"},
          "title": {"bsonType": "string"},  # snapshot
          "unit_price": {"bsonType": ["double", "decimal", "int"]},  # snapshot
          "qty": {"bsonType": ["int", "long"]},
          "variant": {"bsonType": ["object", "null"]}
        }
      }
    },
    "shipping_address": customers_schema["properties"]["addresses"]["items"],  # mesmo formato de address
    "payment_summary": {
      "bsonType": "object",
      "properties": {
        "payment_id": {"bsonType": ["string", "null"]},
        "method": {"enum": ["PIX", "BOLETO", "CREDIT_CARD", "DEBIT_CARD", "WALLET", None]},
        "status": {"enum": ["PENDING", "AUTHORIZED", "CAPTURED", "FAILED", "CANCELLED", None]}
      }
    },
    "total_amount": {"bsonType": ["double", "decimal", "int"]},
    "currency": {"bsonType": "string"},
    "created_at": {"bsonType": "date"},
    "updated_at": {"bsonType": ["date", "null"]}
  }
}

reviews_schema = {
  "bsonType": "object",
  "required": ["review_id", "product_id", "customer_id", "rating", "created_at"],
  "properties": {
    "_id": {},
    "review_id": {"bsonType": "string"},
    "product_id": {"bsonType": "string"},
    "customer_id": {"bsonType": "string"},
    "rating": {"bsonType": ["int", "long"], "minimum": 1, "maximum": 5},
    "comment": {"bsonType": ["string", "null"]},
    "created_at": {"bsonType": "date"}
  }
}

payments_schema = {
  "bsonType": "object",
  "required": ["payment_id", "order_id", "amount", "currency", "method", "status", "created_at"],
  "properties": {
    "_id": {},
    "payment_id": {"bsonType": "string"},
    "order_id": {"bsonType": "string"},
    "amount": {"bsonType": ["double", "decimal", "int"]},
    "currency": {"bsonType": "string"},
    "method": {"enum": ["PIX", "BOLETO", "CREDIT_CARD", "DEBIT_CARD", "WALLET"]},
    "status": {"enum": ["PENDING", "AUTHORIZED", "CAPTURED", "FAILED", "CANCELLED", "REFUNDED"]},
    "provider_ref": {"bsonType": ["string", "null"]},  # id do gateway
    "metadata": {"bsonType": "object"},
    "created_at": {"bsonType": "date"},
    "updated_at": {"bsonType": ["date", "null"]}
  }
}

def main():
    print(f"Conectando em {MONGO_URI}, DB={DB_NAME}")

    # 1) customers
    create_collection_with_schema("customers", customers_schema)
    ensure_indexes("customers", [
        ([("customer_id", ASCENDING)], {"unique": True, "name": "ux_customer_id"}),
        ([("email", ASCENDING)], {"unique": True, "name": "ux_email"})
    ])

    # 2) products
    create_collection_with_schema("products", products_schema)
    ensure_indexes("products", [
        ([("product_id", ASCENDING)], {"unique": True, "name": "ux_product_id"}),
        ([("category", ASCENDING)], {"name": "ix_category"}),
        ([("title", TEXT), ("description", TEXT)], {"name": "txt_title_description"}),
        ([("status", ASCENDING)], {"name": "ix_status"})
    ])

    # 3) carts
    create_collection_with_schema("carts", carts_schema)
    ensure_indexes("carts", [
        ([("customer_id", ASCENDING)], {"unique": True, "name": "ux_customer_cart"}),  # 1 carrinho ativo por cliente
        ([("updated_at", ASCENDING)], {"name": "ix_updated_at"})
    ])

    # 4) orders
    create_collection_with_schema("orders", orders_schema)
    ensure_indexes("orders", [
        ([("order_id", ASCENDING)], {"unique": True, "name": "ux_order_id"}),
        ([("customer_id", ASCENDING), ("created_at", ASCENDING)], {"name": "ix_customer_created"}),
        ([("status", ASCENDING)], {"name": "ix_status"}),
        ([("created_at", ASCENDING)], {"name": "ix_created_at"})
    ])

    # 5) reviews
    create_collection_with_schema("reviews", reviews_schema)
    ensure_indexes("reviews", [
        ([("review_id", ASCENDING)], {"unique": True, "name": "ux_review_id"}),
        ([("product_id", ASCENDING), ("created_at", ASCENDING)], {"name": "ix_product_created"}),
        ([("customer_id", ASCENDING)], {"name": "ix_customer"})
    ])

    # 6) payments
    create_collection_with_schema("payments", payments_schema)
    ensure_indexes("payments", [
        ([("payment_id", ASCENDING)], {"unique": True, "name": "ux_payment_id"}),
        ([("order_id", ASCENDING)], {"name": "ix_order"}),
        ([("status", ASCENDING)], {"name": "ix_status"}),
        ([("created_at", ASCENDING)], {"name": "ix_created_at"})
    ])

    print("\n✅ Coleções, validações e índices criados/atualizados com sucesso.")

if __name__ == "__main__":
    main()
