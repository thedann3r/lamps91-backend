{
    "name": "Admin User",
    "email": "admin@lamps91.com",
    "phone": "0711000001",
    "password": "Admin@123",
    "role": "admin"
}

{
    "email": "admin@lamps91.com",
    "password": "Admin@123"
}

{
    "name": "Finance Officer",
    "email": "finance@lamps91.com",
    "phone": "0711000002",
    "password": "Finance@123",
    "role": "finance_officer"
}

{
    "email": "finance@lamps91.com",
    "password": "Finance@123"
}

{
    "name": "Store Manager",
    "email": "store@lamps91.com",
    "phone": "0711000003",
    "password": "Store@123",
    "role": "store_manager"
}

{
    "email": "store@lamps91.com",
    "password": "Store@123"
}

{
    "name": "Engineer",
    "email": "engineer@lamps91.com",
    "phone": "0711000004",
    "password": "Engineer@123",
    "role": "engineer"
}

{
    "email": "engineer@lamps91.com",
    "password": "Engineer@123"
}

{
    "name": "Sales Officer",
    "email": "sales@lamps91.com",
    "phone": "0711000005",
    "password": "Sales@123",
    "role": "sales_officer"
}

{
    "email": "sales@lamps91.com",
    "password": "Sales@123"
}

{
  "item_code": "TEST-PANEL-001",
  "product_name": "Test Solar Panel",
  "category": "Solar Panels",
  "brand": "TestBrand",
  "unit": "pcs",
  "buying_price": 20000,
  "selling_price": 25000,
  "current_stock": 10,
  "reorder_level": 2
}

{
  "customer_name": "Postman Test Customer",
  "contact_person": "Test Contact",
  "phone": "0799000001",
  "email": "postman.customer@example.com",
  "physical_address": "Test address",
  "county": "Nairobi",
  "customer_type": "commercial"
}

{
  "quote_number": "POSTMAN-Q-20261128-01",
  "customer_id": 1,
  "quote_date": "2026-11-28",
  "valid_until": "2026-12-28",
  "project_name": "Postman Test Installation",
  "site_location": "Nairobi",
  "terms_conditions": "Postman test",
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "unit_price": 24900,
      "discount": 0
    }
  ]
}

# invoices

# {
#   "customer_id": 1,
#   "quotation_id": 1,
#   "so_date": "2026-11-28",
#   "project_name": "Postman Test Installation",
#   "delivery_date": "2026-12-10",
#   "inventory_reserved": false,
#   "installation_team": "Test Team",
#   "status": "pending",
#   "total_amount": 49800,
#   "notes": "Postman test"
# }

{
  "customer_id": 1,
  "sales_order_id": 1,
  "quotation_id": 1,
  "due_date": "2026-12-28",
  "reference": "Postman test",
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "unit_price": 24900,
      "discount": 0
    }
  ]
}

# receipts

{
  "customer_id": 1,
  "invoice_id": 1,
  "payment_method": "mpesa",
  "transaction_reference": "POSTMAN-TRX-001",
  "amount_received": 1000,
  "received_by": "Finance Officer",
  "notes": "Postman receipt test"
}
