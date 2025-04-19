CREATE DATABASE IF NOT EXISTS `pension_db`;
CREATE DATABASE IF NOT EXISTS `food_ration_db`;

-- Grant all privileges to admin user for both databases
GRANT ALL PRIVILEGES ON `pension_db`.* TO 'admin'@'%';
GRANT ALL PRIVILEGES ON `food_ration_db`.* TO 'admin'@'%';
FLUSH PRIVILEGES;