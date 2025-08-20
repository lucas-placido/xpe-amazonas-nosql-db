import os
from pymongo import MongoClient, ASCENDING, TEXT
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI", "mongodb://admin:admin123@localhost:27017/?authSource=admin"
)
# Default já aponta para o novo DB V2
DB_NAME = os.getenv("MONGO_DB", "amazonas-db-v2")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]


def create_collection_with_schema(name: str, schema: dict):
    if name not in db.list_collection_names():
        db.create_collection(name)
        print(f"[OK] Coleção criada: {name}")
    else:
        print(f"[INFO] Coleção já existe: {name}")
    db.command(
        {
            "collMod": name,
            "validator": {"$jsonSchema": schema},
            "validationLevel": "moderate",
        }
    )
    print(f"[OK] Validador aplicado em: {name}")


def ensure_indexes(name: str, indexes: list[tuple]):
    col = db[name]
    for keys, options in indexes:
        col.create_index(keys, **options)
    print(f"[OK] Índices garantidos em: {name}")


# ---------------------------
# Schemas (JSON Schema) — Dimensões
# ---------------------------

customers_schema = {
    "bsonType": "object",
    "required": ["customer_id", "name", "email", "created_at"],
    "properties": {
        "_id": {},
        "customer_id": {"bsonType": "string"},
        "name": {"bsonType": "string"},
        "email": {"bsonType": "string"},
        "phones": {"bsonType": ["array"], "items": {"bsonType": "string"}},
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
                    "is_default": {"bsonType": "bool"},
                },
            },
        },
        "created_at": {"bsonType": "date"},
        "updated_at": {"bsonType": ["date", "null"]},
    },
}

products_schema = {
    "bsonType": "object",
    "required": ["product_id", "title", "price", "category", "created_at"],
    "properties": {
        "_id": {},
        "product_id": {"bsonType": "string"},
        "title": {"bsonType": "string"},
        "description": {"bsonType": ["string", "null"]},
        "category": {"bsonType": "string"},
        "brand": {"bsonType": ["string", "null"]},
        "price": {"bsonType": ["double", "decimal", "int"]},
        "currency": {"bsonType": "string"},
        "images": {"bsonType": ["array"], "items": {"bsonType": "string"}},
        "attributes": {"bsonType": "object"},
        "dimensions": {
            "bsonType": "object",
            "properties": {
                "weight_kg": {"bsonType": ["double", "decimal", "int"]},
                "width_cm": {"bsonType": ["double", "decimal", "int"]},
                "height_cm": {"bsonType": ["double", "decimal", "int"]},
                "depth_cm": {"bsonType": ["double", "decimal", "int"]},
            },
        },
        "stock": {
            "bsonType": "object",
            "properties": {
                "available": {"bsonType": ["int", "long"]},
                "reserved": {"bsonType": ["int", "long"]},
            },
        },
        "status": {"enum": ["ACTIVE", "INACTIVE", "DISCONTINUED"]},
        "created_at": {"bsonType": "date"},
        "updated_at": {"bsonType": ["date", "null"]},
    },
}

# ---------------------------
# Schemas — Coleções operacionais desnormalizadas
# ---------------------------

# Carrinho também carrega snapshot de produto (titulo, category, brand, attributes e price_at_add)
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
                "required": ["product_id", "qty", "product_snapshot"],
                "properties": {
                    "product_id": {"bsonType": "string"},
                    "qty": {"bsonType": ["int", "long"]},
                    "variant": {"bsonType": ["object", "null"]},
                    "product_snapshot": {
                        "bsonType": "object",
                        "required": ["title", "category", "price_at_add", "currency"],
                        "properties": {
                            "title": {"bsonType": "string"},
                            "description": {"bsonType": ["string", "null"]},
                            "category": {"bsonType": "string"},
                            "brand": {"bsonType": ["string", "null"]},
                            "attributes": {"bsonType": "object"},
                            "price_at_add": {"bsonType": ["double", "decimal", "int"]},
                            "currency": {"bsonType": "string"},
                            "images": {
                                "bsonType": ["array"],
                                "items": {"bsonType": "string"},
                            },
                        },
                    },
                },
            },
        },
        "updated_at": {"bsonType": "date"},
    },
}

# Orders carrega snapshot completo de cliente e de cada produto (desnormalização)
orders_schema = {
    "bsonType": "object",
    "required": [
        "order_id",
        "customer_id",
        "customer_snapshot",
        "status",
        "items",
        "total_amount",
        "currency",
        "created_at",
    ],
    "properties": {
        "_id": {},
        "order_id": {"bsonType": "string"},
        "customer_id": {"bsonType": "string"},
        "customer_snapshot": {
            "bsonType": "object",
            "required": ["name", "email"],
            "properties": {
                "customer_id": {"bsonType": ["string", "null"]},
                "name": {"bsonType": "string"},
                "email": {"bsonType": "string"},
                "phones": {"bsonType": ["array"], "items": {"bsonType": "string"}},
                # opcional: endereço padrão do momento do pedido (além de shipping_address)
                "default_address": customers_schema["properties"]["addresses"]["items"],
            },
        },
        "status": {
            "enum": ["PLACED", "PAID", "SHIPPED", "DELIVERED", "CANCELLED", "REFUNDED"]
        },
        "items": {
            "bsonType": "array",
            "items": {
                "bsonType": "object",
                "required": ["product_id", "qty", "product_snapshot"],
                "properties": {
                    "product_id": {"bsonType": "string"},
                    "qty": {"bsonType": ["int", "long"]},
                    "variant": {"bsonType": ["object", "null"]},
                    "product_snapshot": {
                        "bsonType": "object",
                        "required": [
                            "title",
                            "category",
                            "brand",
                            "price_at_order",
                            "currency",
                        ],
                        "properties": {
                            "title": {"bsonType": "string"},
                            "description": {"bsonType": ["string", "null"]},
                            "category": {"bsonType": "string"},
                            "brand": {"bsonType": ["string", "null"]},
                            "attributes": {"bsonType": "object"},
                            "price_at_order": {
                                "bsonType": ["double", "decimal", "int"]
                            },
                            "currency": {"bsonType": "string"},
                            "images": {
                                "bsonType": ["array"],
                                "items": {"bsonType": "string"},
                            },
                            "status": {
                                "enum": ["ACTIVE", "INACTIVE", "DISCONTINUED", None]
                            },
                        },
                    },
                },
            },
        },
        "shipping_address": customers_schema["properties"]["addresses"]["items"],
        "payment_summary": {
            "bsonType": "object",
            "properties": {
                "payment_id": {"bsonType": ["string", "null"]},
                "method": {
                    "enum": [
                        "PIX",
                        "BOLETO",
                        "CREDIT_CARD",
                        "DEBIT_CARD",
                        "WALLET",
                        None,
                    ]
                },
                "status": {
                    "enum": [
                        "PENDING",
                        "AUTHORIZED",
                        "CAPTURED",
                        "FAILED",
                        "CANCELLED",
                        None,
                    ]
                },
            },
        },
        "total_amount": {"bsonType": ["double", "decimal", "int"]},
        "currency": {"bsonType": "string"},
        "created_at": {"bsonType": "date"},
        "updated_at": {"bsonType": ["date", "null"]},
    },
}

# Reviews também carregam snapshots (produto + cliente) para evitar lookups
reviews_schema = {
    "bsonType": "object",
    "required": [
        "review_id",
        "product_id",
        "customer_id",
        "rating",
        "created_at",
        "product_snapshot",
        "customer_snapshot",
    ],
    "properties": {
        "_id": {},
        "review_id": {"bsonType": "string"},
        "product_id": {"bsonType": "string"},
        "customer_id": {"bsonType": "string"},
        "rating": {"bsonType": ["int", "long"], "minimum": 1, "maximum": 5},
        "comment": {"bsonType": ["string", "null"]},
        "product_snapshot": {
            "bsonType": "object",
            "required": ["title", "category", "brand"],
            "properties": {
                "title": {"bsonType": "string"},
                "category": {"bsonType": "string"},
                "brand": {"bsonType": ["string", "null"]},
            },
        },
        "customer_snapshot": {
            "bsonType": "object",
            "required": ["name", "email"],
            "properties": {
                "name": {"bsonType": "string"},
                "email": {"bsonType": "string"},
            },
        },
        "created_at": {"bsonType": "date"},
    },
}

payments_schema = {
    "bsonType": "object",
    "required": [
        "payment_id",
        "order_id",
        "amount",
        "currency",
        "method",
        "status",
        "created_at",
    ],
    "properties": {
        "_id": {},
        "payment_id": {"bsonType": "string"},
        "order_id": {"bsonType": "string"},
        "amount": {"bsonType": ["double", "decimal", "int"]},
        "currency": {"bsonType": "string"},
        "method": {"enum": ["PIX", "BOLETO", "CREDIT_CARD", "DEBIT_CARD", "WALLET"]},
        "status": {
            "enum": [
                "PENDING",
                "AUTHORIZED",
                "CAPTURED",
                "FAILED",
                "CANCELLED",
                "REFUNDED",
            ]
        },
        "provider_ref": {"bsonType": ["string", "null"]},
        "metadata": {"bsonType": "object"},
        "created_at": {"bsonType": "date"},
        "updated_at": {"bsonType": ["date", "null"]},
    },
}


def main():
    print(f"Conectando em {MONGO_URI}, DB={DB_NAME}")

    # Dimensões
    create_collection_with_schema("customers", customers_schema)
    ensure_indexes(
        "customers",
        [
            ([("customer_id", ASCENDING)], {"unique": True, "name": "ux_customer_id"}),
            ([("email", ASCENDING)], {"unique": True, "name": "ux_email"}),
        ],
    )

    create_collection_with_schema("products", products_schema)
    ensure_indexes(
        "products",
        [
            ([("product_id", ASCENDING)], {"unique": True, "name": "ux_product_id"}),
            ([("category", ASCENDING)], {"name": "ix_category"}),
            (
                [("title", TEXT), ("description", TEXT)],
                {"name": "txt_title_description"},
            ),
            ([("status", ASCENDING)], {"name": "ix_status"}),
        ],
    )

    # Operacionais (desnormalizados)
    create_collection_with_schema("carts", carts_schema)
    ensure_indexes(
        "carts",
        [
            (
                [("customer_id", ASCENDING)],
                {"unique": True, "name": "ux_customer_cart"},
            ),
            ([("updated_at", ASCENDING)], {"name": "ix_updated_at"}),
            ([("items.product_id", ASCENDING)], {"name": "ix_items_product"}),
        ],
    )

    create_collection_with_schema("orders", orders_schema)
    ensure_indexes(
        "orders",
        [
            ([("order_id", ASCENDING)], {"unique": True, "name": "ux_order_id"}),
            (
                [("customer_id", ASCENDING), ("created_at", ASCENDING)],
                {"name": "ix_customer_created"},
            ),
            ([("status", ASCENDING)], {"name": "ix_status"}),
            ([("created_at", ASCENDING)], {"name": "ix_created_at"}),
            ([("items.product_id", ASCENDING)], {"name": "ix_items_product"}),
        ],
    )

    create_collection_with_schema("reviews", reviews_schema)
    ensure_indexes(
        "reviews",
        [
            ([("review_id", ASCENDING)], {"unique": True, "name": "ux_review_id"}),
            (
                [("product_id", ASCENDING), ("created_at", ASCENDING)],
                {"name": "ix_product_created"},
            ),
            ([("customer_id", ASCENDING)], {"name": "ix_customer"}),
            # garante 1 review por cliente-produto
            (
                [("product_id", ASCENDING), ("customer_id", ASCENDING)],
                {"unique": True, "name": "ux_product_customer_review"},
            ),
        ],
    )

    create_collection_with_schema("payments", payments_schema)
    ensure_indexes(
        "payments",
        [
            ([("payment_id", ASCENDING)], {"unique": True, "name": "ux_payment_id"}),
            ([("order_id", ASCENDING)], {"name": "ix_order"}),
            ([("status", ASCENDING)], {"name": "ix_status"}),
            ([("created_at", ASCENDING)], {"name": "ix_created_at"}),
        ],
    )

    print(
        "\n✅ amazonas-db-v2 criado com coleções, validações e índices (desnormalizado)."
    )


if __name__ == "__main__":
    main()
