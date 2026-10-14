# Customer Portal Setup

This version adds:
- One login page with Customer / Employee / Shop Owner role selection.
- Customer self-registration.
- Customer product catalogue with current stock and the Product `minimum_selling_price` as the displayed order price.
- Session cart, checkout, order history, and customer cancellation of pending orders.
- Owner/Employee customer-order management.
- Conversion of a customer order into the existing `Sale` model, so the existing stock and reporting system remains the source of truth for actual sales.

## Install/update

1. Copy/replace the project files with this version.
2. Activate the virtual environment.
3. Run:

```powershell
python manage.py check
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

4. Start locally:

```powershell
python manage.py runserver
```

## Production owner

Create the real owner in the production database from the hosting provider's Shell. Do not commit a production database or password to GitHub.

```powershell
python manage.py shell
```

Then:

```python
from django.contrib.auth.models import User, Group

username = "YOUR_OWNER_USERNAME"
password = "YOUR_STRONG_PASSWORD"

owner_group, _ = Group.objects.get_or_create(name="owner")
owner = User.objects.create_user(username=username, password=password)
owner.groups.add(owner_group)
```

The customer group is created automatically when the first customer registers. It can also be created manually:

```python
from django.contrib.auth.models import Group
Group.objects.get_or_create(name="customer")
```

## Important price behavior

The existing Product model contains `minimum_selling_price`, not a normal public/customer selling-price field. Therefore the customer portal displays `minimum_selling_price` and stores that value as the order item's price snapshot.

The existing Sale model still enforces the minimum selling price. If the business later wants a separate public/customer price, add a dedicated `customer_price` field to Product instead of changing the meaning of `minimum_selling_price`.

## Order accounting behavior

Submitting a customer order does NOT create a Sale and does NOT reduce stock. Stock is reduced only when the owner/employee converts the order into the existing Sale records. This prevents unconfirmed customer requests from changing accounting/reporting numbers.
