from app import app, db, Product, PRODUCT_PL, PRODUCT_TW, PRODUCT_UTW, PRODUCT_UC

def seed_products():
    with app.app_context():
        print("Checking for existing products...")
        
        # Define default products
        default_products = [
            {'code': PRODUCT_PL, 'name': 'Personal Loan'},
            {'code': PRODUCT_TW, 'name': 'Two Wheeler'},
            {'code': PRODUCT_UTW, 'name': 'Used Two Wheeler'},
            {'code': PRODUCT_UC, 'name': 'Used Car'}
        ]
        
        # Add each product if it doesn't exist
        for product_data in default_products:
            existing_product = Product.query.filter_by(code=product_data['code']).first()
            if not existing_product:
                print(f"Adding product: {product_data['name']} ({product_data['code']})")
                product = Product(
                    code=product_data['code'],
                    name=product_data['name'],
                    active=True
                )
                db.session.add(product)
            else:
                print(f"Product already exists: {existing_product.name} ({existing_product.code})")
        
        db.session.commit()
        print("Product seeding completed!")

if __name__ == "__main__":
    seed_products()
