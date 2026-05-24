
SET NAMES utf8mb4;
SET collation_connection = 'utf8mb4_unicode_ci';

/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
DROP TABLE IF EXISTS `ws_control`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4*/;
CREATE TABLE `ws_control` (
  `clave` varchar(50) NOT NULL,
  `valor` varchar(100) DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`clave`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ws_devices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4*/;
CREATE TABLE `ws_devices` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `device_id` text DEFAULT NULL,
  `tipo` text DEFAULT NULL,
  `nombre` text DEFAULT NULL,
  `ip` text DEFAULT NULL,
  `mac` text DEFAULT NULL,
  `estado` int(11) DEFAULT 1,
  `token` text DEFAULT NULL,
  `last_seen` datetime DEFAULT NULL,
  `sucursal_id` int(11) DEFAULT NULL,
  `cedula` varchar(20) DEFAULT NULL,
  `terminal_id` int(11) DEFAULT 1,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ws_servers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4*/;
CREATE TABLE `ws_servers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mac` varchar(32) DEFAULT NULL,
  `hostname` varchar(100) DEFAULT NULL,
  `ip_local` varchar(45) DEFAULT NULL,
  `os` varchar(20) DEFAULT NULL,
  `version` varchar(20) DEFAULT NULL,
  `app` varchar(50) DEFAULT NULL,
  `token` varchar(128) DEFAULT NULL,
  `activo` tinyint(4) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `last_seen` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mac` (`mac`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ws_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4*/;
CREATE TABLE `ws_settings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `setting_key` varchar(50) NOT NULL,
  `setting_value` text NOT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `setting_key` (`setting_key`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ws_sucursales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4*/;
CREATE TABLE `ws_sucursales` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ws_server_id` int(11) DEFAULT NULL,
  `idsucursal` int(11) DEFAULT NULL,
  `cedula` varchar(20) DEFAULT NULL,
  `razon` varchar(150) DEFAULT NULL,
  `access_token` text DEFAULT NULL,
  `activo` tinyint(4) DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `ws_server_id` (`ws_server_id`),
  CONSTRAINT `ws_sucursales_ibfk_1` FOREIGN KEY (`ws_server_id`) REFERENCES `ws_servers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

