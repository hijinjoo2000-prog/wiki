export PAYPAL_CLIENT_ID=$(grep 'PAYPAL_CLIENT_ID' .env | cut -d= -f2)
export PAYPAL_SECRET=$(grep 'PAYPAL_SECRET' .env | cut -d= -f2)
export DATABASE_URL=$(grep 'DATABASE_URL' .env | cut -d= -f2)