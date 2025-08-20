import os
import uuid
import random
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:admin123@localhost:27017/?authSource=admin")
DB_NAME = os.getenv("MONGO_DB", "amazonas")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def random_uuid():
    return str(uuid.uuid4())

def seed_customers():
    customers = [
        {
            "customer_id": random_uuid(),
            "name": "Lucas Almeida",
            "email": "lucas.almeida@example.com",
            "phones": ["+55 11 91234-5678"],
            "addresses": [{
                "label": "Casa",
                "street": "Rua das Flores",
                "number": "123",
                "district": "Jardim Primavera",
                "city": "São Paulo",
                "state": "SP",
                "zip": "01001-000",
                "country": "Brasil",
                "is_default": True
            }],
            "created_at": datetime.utcnow(),
            "updated_at": None
        },
        {
            "customer_id": random_uuid(),
            "name": "Maria Souza",
            "email": "maria.souza@example.com",
            "phones": ["+55 21 99876-5432"],
            "addresses": [{
                "label": "Trabalho",
                "street": "Av. Atlântica",
                "number": "500",
                "district": "Copacabana",
                "city": "Rio de Janeiro",
                "state": "RJ",
                "zip": "22010-000",
                "country": "Brasil",
                "is_default": True
            }],
            "created_at": datetime.utcnow(),
            "updated_at": None
        }
    ]
    db.customers.insert_many(customers)
    print("[OK] Clientes inseridos")

def seed_products():
    products = [
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
            "updated_at": None
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
            "updated_at": None
        }
    ]
    db.products.insert_many(products)
    print("[OK] Produtos inseridos")

def seed_carts():
    customers = list(db.customers.find({}, {"customer_id": 1}))
    products = list(db.products.find({}, {"product_id": 1, "title": 1, "price": 1}))
    carts = []

    for cust in customers:
        product = random.choice(products)
        carts.append({
            "customer_id": cust["customer_id"],
            "items": [{
                "product_id": product["product_id"],
                "title": product["title"],
                "unit_price": product["price"],
                "qty": 1
            }],
            "updated_at": datetime.utcnow()
        })
    db.carts.insert_many(carts)
    print("[OK] Carrinhos inseridos")

def seed_orders():
    customers = list(db.customers.find({}, {"customer_id": 1, "addresses": 1}))
    products = list(db.products.find({}, {"product_id": 1, "title": 1, "price": 1}))
    orders = []

    for cust in customers:
        product = random.choice(products)
        orders.append({
            "order_id": random_uuid(),
            "customer_id": cust["customer_id"],
            "status": "PLACED",
            "items": [{
                "product_id": product["product_id"],
                "title": product["title"],
                "unit_price": product["price"],
                "qty": 2
            }],
            "shipping_address": cust["addresses"][0],
            "payment_summary": {
                "payment_id": None,
                "method": "CREDIT_CARD",
                "status": "PENDING"
            },
            "total_amount": product["price"] * 2,
            "currency": "BRL",
            "created_at": datetime.utcnow(),
            "updated_at": None
        })
    db.orders.insert_many(orders)
    print("[OK] Pedidos inseridos")

def seed_reviews():
    customers = list(db.customers.find({}, {"customer_id": 1}))
    products = list(db.products.find({}, {"product_id": 1}))
    reviews = []

    for cust in customers:
        product = random.choice(products)
        reviews.append({
            "review_id": random_uuid(),
            "product_id": product["product_id"],
            "customer_id": cust["customer_id"],
            "rating": random.randint(3, 5),
            "comment": "Produto excelente, recomendo!",
            "created_at": datetime.utcnow()
        })
    db.reviews.insert_many(reviews)
    print("[OK] Avaliações inseridas")

def seed_payments():
    orders = list(db.orders.find({}, {"order_id": 1, "total_amount": 1}))
    payments = []

    for order in orders:
        payments.append({
            "payment_id": random_uuid(),
            "order_id": order["order_id"],
            "amount": order["total_amount"],
            "currency": "BRL",
            "method": "CREDIT_CARD",
            "status": "AUTHORIZED",
            "provider_ref": "PAY-" + str(random.randint(10000, 99999)),
            "metadata": {"parcelas": 3},
            "created_at": datetime.utcnow(),
            "updated_at": None
        })
    db.payments.insert_many(payments)
    print("[OK] Pagamentos inseridos")

def main():
    seed_customers()
    seed_products()
    seed_carts()
    seed_orders()
    seed_reviews()
    seed_payments()
    print("\n✅ Dados de exemplo inseridos com sucesso.")

if __name__ == "__main__":
    main()
