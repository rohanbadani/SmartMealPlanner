CREATE DATABASE IF NOT EXISTS mealapp;
USE mealapp;

DROP TABLE IF EXISTS inventory;

CREATE TABLE inventory (
  name VARCHAR(64) NOT NULL,
  quantity INT NOT NULL,
  day INT NOT NULL,
  month INT NOT NULL,
  year INT NOT NULL,
  PRIMARY KEY (name)
);

DROP USER IF EXISTS 'mealapp-read-only';
DROP USER IF EXISTS 'mealapp-read-write';
CREATE USER 'mealapp-read-only' IDENTIFIED BY 'abc123!!';
CREATE USER 'mealapp-read-write' IDENTIFIED BY 'def456!!';
GRANT SELECT, SHOW VIEW ON mealapp.* 
TO 'mealapp-read-only';
GRANT SELECT, SHOW VIEW, INSERT, UPDATE, DELETE, DROP, CREATE, ALTER ON mealapp.* 
TO 'mealapp-read-write';
FLUSH PRIVILEGES;

USE mealapp;
INSERT INTO inventory (name, quantity, day, month, year) VALUES ('Milk', 2, 10, 3, 2025);
INSERT INTO inventory (name, quantity, day, month, year) VALUES ('Eggs', 12, 15, 3, 2025);
INSERT INTO inventory (name, quantity, day, month, year) VALUES ('Bread', 1, 5, 4, 2025);
INSERT INTO inventory (name, quantity, day, month, year) VALUES ('Apples', 10, 20, 3, 2025);
INSERT INTO inventory (name, quantity, day, month, year) VALUES ('Chicken', 2, 25, 3, 2025);

USE mealapp;
SELECT * FROM inventory;
