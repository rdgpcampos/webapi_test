CREATE TABLE IF NOT EXISTS orders (
	order_id SERIAL PRIMARY KEY,
	client_id VARCHAR( 50 ) NOT NULL,
	status VARCHAR( 50 ) NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
	product_id SERIAL PRIMARY KEY,
	order_id INT,
	description VARCHAR( 250 ),
	unit_price DECIMAL(12,2),
	FOREIGN KEY (order_id) REFERENCES orders(order_id),
	CHECK (unit_price >= 0)
);