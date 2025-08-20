import os
import uuid
import random
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI", "mongodb://admin:admin123@localhost:27017/?authSource=admin"
)
DB_NAME = os.getenv("MONGO_DB", "amazonas-db-v2")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]


def uid():
    return str(uuid.uuid4())


def seed_customers():
    docs = [
        {
            "customer_id": uid(),
            "name": "Lucas Almeida",
            "email": "lucas.almeida@example.com",
            "phones": ["+55 11 91234-5678"],
            "addresses": [
                {
                    "label": "Casa",
                    "street": "Rua das Flores",
                    "number": "123",
                    "district": "Jardim Primavera",
                    "city": "São Paulo",
                    "state": "SP",
                    "zip": "01001-000",
                    "country": "Brasil",
                    "is_default": True,
                }
            ],
            "created_at": datetime.utcnow(),
            "updated_at": None,
        },
        {
            "customer_id": uid(),
            "name": "Maria Souza",
            "email": "maria.souza@example.com",
            "phones": ["+55 21 99876-5432"],
            "addresses": [
                {
                    "label": "Trabalho",
                    "street": "Av. Atlântica",
                    "number": "500",
                    "district": "Copacabana",
                    "city": "Rio de Janeiro",
                    "state": "RJ",
                    "zip": "22010-000",
                    "country": "Brasil",
                    "is_default": True,
                }
            ],
            "created_at": datetime.utcnow(),
            "updated_at": None,
        },
    ]
    db.customers.insert_many(docs)
    print("[OK] customers")


def seed_products():
    docs = [
        {
            "product_id": "SKU-001",
            "title": "Smartphone Galaxy S25",
            "description": "Smartphone de última geração com câmera tripla",
            "category": "Eletrônicos",
            "brand": "Samsung",
            "price": 3999.90,
            "currency": "BRL",
            "images": ["https://example.com/img/galaxy.jpg"],
            "attributes": {"cor": "Preto", "memoria": "256GB"},
            "stock": {"available": 50, "reserved": 0},
            "status": "ACTIVE",
            "created_at": datetime.utcnow(),
            "updated_at": None,
        },
        {
            "product_id": "SKU-002",
            "title": "Tênis Nike Air",
            "description": "Tênis esportivo confortável e estiloso",
            "category": "Vestuário",
            "brand": "Nike",
            "price": 499.90,
            "currency": "BRL",
            "images": ["https://example.com/img/nikeair.jpg"],
            "attributes": {"cor": "Branco", "tamanho": "42"},
            "stock": {"available": 120, "reserved": 5},
            "status": "ACTIVE",
            "created_at": datetime.utcnow(),
            "updated_at": None,
        },
    ]
    db.products.insert_many(docs)
    print("[OK] products")


def default_address_of(customer):
    if not customer.get("addresses"):
        return None
    for a in customer["addresses"]:
        if a.get("is_default"):
            return a
    return customer["addresses"][0]


def seed_carts():
    customers = list(db.customers.find({}, {"customer_id": 1, "name": 1, "email": 1}))
    products = list(db.products.find({}, {"_id": 0}))
    docs = []

    for cust in customers:
        p = random.choice(products)
        docs.append(
            {
                "customer_id": cust["customer_id"],
                "items": [
                    {
                        "product_id": p["product_id"],
                        "qty": random.randint(1, 2),
                        "variant": None,
                        "product_snapshot": {
                            "title": p["title"],
                            "description": p.get("description"),
                            "category": p["category"],
                            "brand": p.get("brand"),
                            "attributes": p.get("attributes", {}),
                            "price_at_add": p["price"],
                            "currency": p.get("currency", "BRL"),
                            "images": p.get("images", []),
                        },
                    }
                ],
                "updated_at": datetime.utcnow(),
            }
        )
    db.carts.insert_many(docs)
    print("[OK] carts")


def seed_orders():
    customers = list(db.customers.find({}, {"_id": 0}))
    products = list(db.products.find({}, {"_id": 0}))
    docs = []

    for cust in customers:
        prod = random.choice(products)
        qty = random.randint(1, 3)
        price_at_order = prod["price"]  # snapshot do preço no momento do pedido
        total = price_at_order * qty

        docs.append(
            {
                "order_id": uid(),
                "customer_id": cust["customer_id"],
                "customer_snapshot": {
                    "customer_id": cust["customer_id"],
                    "name": cust["name"],
                    "email": cust["email"],
                    "phones": cust.get("phones", []),
                    "default_address": default_address_of(cust),
                },
                "status": "PLACED",
                "items": [
                    {
                        "product_id": prod["product_id"],
                        "qty": qty,
                        "variant": None,
                        "product_snapshot": {
                            "title": prod["title"],
                            "description": prod.get("description"),
                            "category": prod["category"],
                            "brand": prod.get("brand"),
                            "attributes": prod.get("attributes", {}),
                            "price_at_order": price_at_order,
                            "currency": prod.get("currency", "BRL"),
                            "images": prod.get("images", []),
                            "status": prod.get("status"),
                        },
                    }
                ],
                "shipping_address": default_address_of(cust),
                "payment_summary": {
                    "payment_id": None,
                    "method": "CREDIT_CARD",
                    "status": "PENDING",
                },
                "total_amount": total,
                "currency": "BRL",
                "created_at": datetime.utcnow(),
                "updated_at": None,
            }
        )
    db.orders.insert_many(docs)
    print("[OK] orders")


def seed_reviews():
    customers = list(db.customers.find({}, {"_id": 0}))
    products = list(db.products.find({}, {"_id": 0}))
    docs = []

    for cust in customers:
        prod = random.choice(products)
        docs.append(
            {
                "review_id": uid(),
                "product_id": prod["product_id"],
                "customer_id": cust["customer_id"],
                "rating": random.randint(3, 5),
                "comment": "Entrega rápida e produto conforme descrição.",
                "product_snapshot": {
                    "title": prod["title"],
                    "category": prod["category"],
                    "brand": prod.get("brand"),
                },
                "customer_snapshot": {"name": cust["name"], "email": cust["email"]},
                "created_at": datetime.utcnow(),
            }
        )
    # Evita violar índice único product_id+customer_id (em caso de reexecução)
    # Aqui poderíamos fazer upsert por par (product_id, customer_id). Para simplicidade, try/except:
    try:
        db.reviews.insert_many(docs, ordered=False)
    except Exception as e:
        print(f"[WARN] reviews: possíveis duplicatas ignoradas: {e}")
    print("[OK] reviews")


def seed_payments():
    orders = list(
        db.orders.find({}, {"_id": 0, "order_id": 1, "total_amount": 1, "currency": 1})
    )
    docs = []
    for o in orders:
        docs.append(
            {
                "payment_id": uid(),
                "order_id": o["order_id"],
                "amount": o["total_amount"],
                "currency": o.get("currency", "BRL"),
                "method": "CREDIT_CARD",
                "status": "AUTHORIZED",
                "provider_ref": f"PAY-{random.randint(10000, 99999)}",
                "metadata": {"parcelas": random.choice([1, 2, 3])},
                "created_at": datetime.utcnow(),
                "updated_at": None,
            }
        )
    db.payments.insert_many(docs)
    print("[OK] payments")


def main():
    seed_customers()
    seed_products()
    seed_carts()
    seed_orders()
    seed_reviews()
    seed_payments()
    print("\n✅ Seed V2 concluído com snapshots desnormalizados.")


if __name__ == "__main__":
    main()
