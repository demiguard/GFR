-- MySQL dump 10.13  Distrib 8.0.17, for Linux (x86_64)
--
-- Host: localhost    Database: gfrdb
-- ------------------------------------------------------
-- Server version	8.0.17

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add config',1,'add_config'),(2,'Can change config',1,'change_config'),(3,'Can delete config',1,'delete_config'),(4,'Can view config',1,'view_config'),(5,'Can add handled examinations',2,'add_handledexaminations'),(6,'Can change handled examinations',2,'change_handledexaminations'),(7,'Can delete handled examinations',2,'delete_handledexaminations'),(8,'Can view handled examinations',2,'view_handledexaminations'),(9,'Can add hospital',3,'add_hospital'),(10,'Can change hospital',3,'change_hospital'),(11,'Can delete hospital',3,'delete_hospital'),(12,'Can view hospital',3,'view_hospital'),(13,'Can add procedure type',4,'add_proceduretype'),(14,'Can change procedure type',4,'change_proceduretype'),(15,'Can delete procedure type',4,'delete_proceduretype'),(16,'Can view procedure type',4,'view_proceduretype'),(17,'Can add user group',5,'add_usergroup'),(18,'Can change user group',5,'change_usergroup'),(19,'Can delete user group',5,'delete_usergroup'),(20,'Can view user group',5,'view_usergroup'),(21,'Can add department',6,'add_department'),(22,'Can change department',6,'change_department'),(23,'Can delete department',6,'delete_department'),(24,'Can view department',6,'view_department'),(25,'Can add user',7,'add_user'),(26,'Can change user',7,'change_user'),(27,'Can delete user',7,'delete_user'),(28,'Can view user',7,'view_user'),(29,'Can add address',8,'add_address'),(30,'Can change address',8,'change_address'),(31,'Can delete address',8,'delete_address'),(32,'Can view address',8,'view_address'),(33,'Can add server configuration',9,'add_serverconfiguration'),(34,'Can change server configuration',9,'change_serverconfiguration'),(35,'Can delete server configuration',9,'delete_serverconfiguration'),(36,'Can view server configuration',9,'view_serverconfiguration'),(37,'Can add log entry',10,'add_logentry'),(38,'Can change log entry',10,'change_logentry'),(39,'Can delete log entry',10,'delete_logentry'),(40,'Can view log entry',10,'view_logentry'),(41,'Can add permission',11,'add_permission'),(42,'Can change permission',11,'change_permission'),(43,'Can delete permission',11,'delete_permission'),(44,'Can view permission',11,'view_permission'),(45,'Can add group',12,'add_group'),(46,'Can change group',12,'change_group'),(47,'Can delete group',12,'delete_group'),(48,'Can view group',12,'view_group'),(49,'Can add content type',13,'add_contenttype'),(50,'Can change content type',13,'change_contenttype'),(51,'Can delete content type',13,'delete_contenttype'),(52,'Can view content type',13,'view_contenttype'),(53,'Can add session',14,'add_session'),(54,'Can change session',14,'change_session'),(55,'Can delete session',14,'delete_session'),(56,'Can view session',14,'view_session');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_main_page_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_main_page_user_id` FOREIGN KEY (`user_id`) REFERENCES `main_page_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (10,'admin','logentry'),(12,'auth','group'),(11,'auth','permission'),(13,'contenttypes','contenttype'),(8,'main_page','address'),(1,'main_page','config'),(6,'main_page','department'),(2,'main_page','handledexaminations'),(3,'main_page','hospital'),(4,'main_page','proceduretype'),(9,'main_page','serverconfiguration'),(7,'main_page','user'),(5,'main_page','usergroup'),(14,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'main_page','0001_initial','2020-07-01 12:41:14.968647'),(2,'contenttypes','0001_initial','2020-07-01 12:41:18.651302'),(3,'admin','0001_initial','2020-07-01 12:41:18.917837'),(4,'admin','0002_logentry_remove_auto_add','2020-07-01 12:41:19.928441'),(5,'admin','0003_logentry_add_action_flag_choices','2020-07-01 12:41:19.962299'),(6,'contenttypes','0002_remove_content_type_name','2020-07-01 12:41:20.743196'),(7,'auth','0001_initial','2020-07-01 12:41:21.361634'),(8,'auth','0002_alter_permission_name_max_length','2020-07-01 12:41:23.275241'),(9,'auth','0003_alter_user_email_max_length','2020-07-01 12:41:23.309727'),(10,'auth','0004_alter_user_username_opts','2020-07-01 12:41:23.362939'),(11,'auth','0005_alter_user_last_login_null','2020-07-01 12:41:23.402743'),(12,'auth','0006_require_contenttypes_0002','2020-07-01 12:41:23.428925'),(13,'auth','0007_alter_validators_add_error_messages','2020-07-01 12:41:23.462670'),(14,'auth','0008_alter_user_username_max_length','2020-07-01 12:41:23.494642'),(15,'auth','0009_alter_user_last_name_max_length','2020-07-01 12:41:23.542617'),(16,'auth','0010_alter_group_name_max_length','2020-07-01 12:41:23.653312'),(17,'auth','0011_update_proxy_permissions','2020-07-01 12:41:23.693834'),(18,'main_page','0002_hospital_short_name','2020-07-01 12:41:23.861407'),(19,'main_page','0003_auto_20190712_1425','2020-07-01 12:41:23.887958'),(20,'main_page','0004_auto_20190719_1329','2020-07-01 12:41:25.070945'),(21,'main_page','0005_address_serverconfiguration','2020-07-01 12:41:25.421821'),(22,'main_page','0006_auto_20200629_1609','2020-07-01 12:41:28.902831'),(23,'sessions','0001_initial','2020-07-01 12:41:29.159819');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('3tu5a7v0orx18023larn9ja8x9741fur','NDlhMzRkMDI4MzhlYWU0MjgxY2UxYmYwMjI5NmFhMWYxODkzZjhkZDp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoibWFpbl9wYWdlLmJhY2tlbmRzLlNpbXBsZUJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiJiZWIyNTY0ZTg5ODliNmE5ZmViM2Q3MzUxMDM3MjlmOWZlMThjMTE5In0=','2020-07-15 13:08:07.373958'),('60d6x4mbqrbmn0xy6i8s997b61w6jbln','NDlhMzRkMDI4MzhlYWU0MjgxY2UxYmYwMjI5NmFhMWYxODkzZjhkZDp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoibWFpbl9wYWdlLmJhY2tlbmRzLlNpbXBsZUJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiJiZWIyNTY0ZTg5ODliNmE5ZmViM2Q3MzUxMDM3MjlmOWZlMThjMTE5In0=','2020-07-15 13:08:07.545962'),('cqs186vi0wf6fcwi1ir2a508243j8rxi','NDlhMzRkMDI4MzhlYWU0MjgxY2UxYmYwMjI5NmFhMWYxODkzZjhkZDp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoibWFpbl9wYWdlLmJhY2tlbmRzLlNpbXBsZUJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiJiZWIyNTY0ZTg5ODliNmE5ZmViM2Q3MzUxMDM3MjlmOWZlMThjMTE5In0=','2020-07-17 06:45:42.952537'),('h7xkf0dq0t31ctmp2sp1uxtdmqv8qhk0','NDlhMzRkMDI4MzhlYWU0MjgxY2UxYmYwMjI5NmFhMWYxODkzZjhkZDp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoibWFpbl9wYWdlLmJhY2tlbmRzLlNpbXBsZUJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiJiZWIyNTY0ZTg5ODliNmE5ZmViM2Q3MzUxMDM3MjlmOWZlMThjMTE5In0=','2020-07-15 13:10:06.312742'),('p4ujoqpck0dxwf8vwjj0tqqwidt8gphp','MjJmNjI0NjY3Y2U4NzJiNTA0MDM3MjI0MjAxMGMxODgxMjc2NDg0ZDp7Il9hdXRoX3VzZXJfaWQiOiI3IiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoibWFpbl9wYWdlLmJhY2tlbmRzLlNpbXBsZUJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiJhZDJkZDBkNzk3MTk3ZjdiNDY4NDg0MTg2YWVmMDEwNGFlNjNjZmVjIn0=','2020-07-16 09:04:54.065605');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `main_page_address`
--

DROP TABLE IF EXISTS `main_page_address`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `main_page_address` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ae_title` varchar(16) DEFAULT NULL,
  `ip` varchar(20) NOT NULL,
  `port` varchar(5) NOT NULL,
  `description` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_page_address`
--

LOCK TABLES `main_page_address` WRITE;
/*!40000 ALTER TABLE `main_page_address` DISABLE KEYS */;
INSERT INTO `main_page_address` VALUES (1,'VIMCM','10.143.128.247','3320','RIS'),(2,'VIPDICOM','10.143.128.234','104','PACS');
/*!40000 ALTER TABLE `main_page_address` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `main_page_config`
--

DROP TABLE IF EXISTS `main_page_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `main_page_config` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ris_calling` varchar(200) NOT NULL,
  `black_list` tinyint(1) NOT NULL,
  `pacs_id` int(11) DEFAULT NULL,
  `ris_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `main_page_config_pacs_id_800b6705_fk_main_page_address_id` (`pacs_id`),
  KEY `main_page_config_ris_id_cedcc7e1_fk_main_page_address_id` (`ris_id`),
  CONSTRAINT `main_page_config_pacs_id_800b6705_fk_main_page_address_id` FOREIGN KEY (`pacs_id`) REFERENCES `main_page_address` (`id`),
  CONSTRAINT `main_page_config_ris_id_cedcc7e1_fk_main_page_address_id` FOREIGN KEY (`ris_id`) REFERENCES `main_page_address` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_page_config`
--

LOCK TABLES `main_page_config` WRITE;
/*!40000 ALTER TABLE `main_page_config` DISABLE KEYS */;
INSERT INTO `main_page_config` VALUES (1,'TEST_AET',1,NULL,NULL),(2,'RH_EDTA',1,2,1),(3,'HEHKFARGHOTR05',1,2,1),(4,'EDTA_GLO',1,2,1),(5,'HVHFBERGHK7',1,2,1),(6,'HIKFARGFR13',1,2,1),(7,'NOTIMPLEMENTED',1,NULL,NULL),(8,'BFHKFNMGFR1',1,2,1);
/*!40000 ALTER TABLE `main_page_config` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `main_page_config_accepted_procedures`
--

DROP TABLE IF EXISTS `main_page_config_accepted_procedures`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `main_page_config_accepted_procedures` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `config_id` int(11) NOT NULL,
  `proceduretype_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `main_page_config_accepte_config_id_proceduretype__7a1ca848_uniq` (`config_id`,`proceduretype_id`),
  KEY `main_page_config_acc_proceduretype_id_e80e09d1_fk_main_page` (`proceduretype_id`),
  CONSTRAINT `main_page_config_acc_config_id_f813e21c_fk_main_page` FOREIGN KEY (`config_id`) REFERENCES `main_page_config` (`id`),
  CONSTRAINT `main_page_config_acc_proceduretype_id_e80e09d1_fk_main_page` FOREIGN KEY (`proceduretype_id`) REFERENCES `main_page_proceduretype` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_page_config_accepted_procedures`
--

LOCK TABLES `main_page_config_accepted_procedures` WRITE;
/*!40000 ALTER TABLE `main_page_config_accepted_procedures` DISABLE KEYS */;
INSERT INTO `main_page_config_accepted_procedures` VALUES (1,1,6),(2,2,5),(3,2,7);
/*!40000 ALTER TABLE `main_page_config_accepted_procedures` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `main_page_department`
--

DROP TABLE IF EXISTS `main_page_department`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `main_page_department` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) DEFAULT NULL,
  `thining_factor` double DEFAULT NULL,
  `thining_factor_change_date` date NOT NULL,
  `config_id` int(11) DEFAULT NULL,
  `hospital_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `config_id` (`config_id`),
  KEY `main_page_department_hospital_id_a89d9847_fk_main_page` (`hospital_id`),
  CONSTRAINT `main_page_department_config_id_be81f97f_fk_main_page_config_id` FOREIGN KEY (`config_id`) REFERENCES `main_page_config` (`id`),
  CONSTRAINT `main_page_department_hospital_id_a89d9847_fk_main_page` FOREIGN KEY (`hospital_id`) REFERENCES `main_page_hospital` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_page_department`
--

LOCK TABLES `main_page_department` WRITE;
/*!40000 ALTER TABLE `main_page_department` DISABLE KEYS */;
INSERT INTO `main_page_department` VALUES (1,'test_department',5442,'2020-05-18',1,1),(2,'Klin. Fys.',3550,'2020-06-29',2,2),(3,'Klin. Fys.',0,'0001-01-01',3,3),(4,'Klin. Fys.',2336,'2020-06-30',4,4),(5,'Klin. Fys.',0,'0001-01-01',5,5),(6,'',0,'0001-01-01',6,6),(7,'',0,'0001-01-01',7,7),(8,'',0,'0001-01-01',8,8);
/*!40000 ALTER TABLE `main_page_department` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `main_page_handledexaminations`
--

DROP TABLE IF EXISTS `main_page_handledexaminations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `main_page_handledexaminations` (
  `accession_number` varchar(20) NOT NULL,
  `handle_day` date NOT NULL,
  PRIMARY KEY (`accession_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_page_handledexaminations`
--

LOCK TABLES `main_page_handledexaminations` WRITE;
/*!40000 ALTER TABLE `main_page_handledexaminations` DISABLE KEYS */;
INSERT INTO `main_page_handledexaminations` VALUES ('45654','2020-06-29'),('REGH13860887','2020-06-29'),('REGH13861006','2020-06-29'),('REGH14230958','2020-06-29'),('REGH14302429','2020-06-29'),('REGH14490554','2020-06-29'),('REGH14515618','2020-06-29'),('REGH14515623','2020-06-29');
/*!40000 ALTER TABLE `main_page_handledexaminations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `main_page_hospital`
--

DROP TABLE IF EXISTS `main_page_hospital`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `main_page_hospital` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) DEFAULT NULL,
  `address` varchar(200) DEFAULT NULL,
  `short_name` varchar(8) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_page_hospital`
--

LOCK TABLES `main_page_hospital` WRITE;
/*!40000 ALTER TABLE `main_page_hospital` DISABLE KEYS */;
INSERT INTO `main_page_hospital` VALUES (1,'test_hospital','','TEST'),(2,'Rigshospitalet','Blegdamsvej 9, 2100 København','RH'),(3,'Herlev Hospital','Borgmester Ib Juuls Vej 1, 2730 Herlev','HEH'),(4,'Rigshospitalet, Glostrup','Valdemar Hansens Vej 1-23, 2600 Glostrup','GLO'),(5,'Hvidovre Hospital','Kettegård Alle 30, 2650 Hvidovre','HVH'),(6,'Hillerød hospital','','HI'),(7,'Frederiksberg hospital','','FH'),(8,'Bispebjerg hospital','','BH');
/*!40000 ALTER TABLE `main_page_hospital` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `main_page_proceduretype`
--

DROP TABLE IF EXISTS `main_page_proceduretype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `main_page_proceduretype` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `type_name` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_page_proceduretype`
--

LOCK TABLES `main_page_proceduretype` WRITE;
/*!40000 ALTER TABLE `main_page_proceduretype` DISABLE KEYS */;
INSERT INTO `main_page_proceduretype` VALUES (1,'asdfqew'),(2,'zxcvasdfwer'),(3,'uiopjkl'),(4,'asdf'),(5,'wqer'),(6,'asdfqwer'),(7,'Clearance blodprøve 2. gang');
/*!40000 ALTER TABLE `main_page_proceduretype` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `main_page_serverconfiguration`
--

DROP TABLE IF EXISTS `main_page_serverconfiguration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `main_page_serverconfiguration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `samba_ip` varchar(20) NOT NULL,
  `samba_name` varchar(30) NOT NULL,
  `samba_user` varchar(30) NOT NULL,
  `samba_pass` varchar(30) NOT NULL,
  `samba_pc` varchar(30) NOT NULL,
  `samba_share` varchar(30) NOT NULL,
  `AE_title` varchar(30) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_page_serverconfiguration`
--

LOCK TABLES `main_page_serverconfiguration` WRITE;
/*!40000 ALTER TABLE `main_page_serverconfiguration` DISABLE KEYS */;
INSERT INTO `main_page_serverconfiguration` VALUES (1,'10.49.144.11','gfr','gfr','gfr','gfr','data','RHKFANMGFR2');
/*!40000 ALTER TABLE `main_page_serverconfiguration` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `main_page_user`
--

DROP TABLE IF EXISTS `main_page_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `main_page_user` (
  `last_login` datetime(6) DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(120) NOT NULL,
  `password` varchar(120) NOT NULL,
  `department_id` int(11) DEFAULT NULL,
  `user_group_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `main_page_user_department_id_361f79f5_fk_main_page_department_id` (`department_id`),
  KEY `main_page_user_user_group_id_2672a990_fk_main_page_usergroup_id` (`user_group_id`),
  CONSTRAINT `main_page_user_department_id_361f79f5_fk_main_page_department_id` FOREIGN KEY (`department_id`) REFERENCES `main_page_department` (`id`),
  CONSTRAINT `main_page_user_user_group_id_2672a990_fk_main_page_usergroup_id` FOREIGN KEY (`user_group_id`) REFERENCES `main_page_usergroup` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_page_user`
--

LOCK TABLES `main_page_user` WRITE;
/*!40000 ALTER TABLE `main_page_user` DISABLE KEYS */;
INSERT INTO `main_page_user` VALUES ('2020-07-03 06:45:42.916102',1,'test_admin','pbkdf2_sha256$150000$vcYlwpYHUwWX$0iGzlfYr/gIYrY4Ul4AyVXEeUG429G0H8cG+VMbr2yM=',1,1),('2019-07-17 06:03:32.689000',2,'test_user','pbkdf2_sha256$150000$dYbVvh70LR2z$FDFZoERcmbJS0fkCKtXRIToF66JfrTWJIWCi9NdBXmg=',1,2),('2020-07-02 09:04:19.502791',3,'rh_test','pbkdf2_sha256$150000$VkAzHkBimug6$fXuUuSPz+5+pfIAaVMqOJjMoGzIIL5TRhZjcOczdnbU=',2,2),('2020-07-01 08:39:18.061000',4,'pacs_test','pbkdf2_sha256$150000$q3eHzWmwWz3j$BMCpEBcun6l41uSc/IEqFEqtUq9xM7FQ1CDp4Plt0WA=',2,2),('2019-08-21 06:13:51.084000',5,'sauron','pbkdf2_sha256$150000$VgpbYIfVF3D7$ARNsNM2mZm/Ubabn//VOuun0tb0xvlRzp3kl9CMgaFA=',2,1),(NULL,6,'heh_test','pbkdf2_sha256$150000$X19MhukI89E2$LP1ePIEFFncnZ2huOM41E6TVRiphaPqjKSKeQHsES2k=',3,2),('2020-07-02 09:04:54.037281',7,'glo_test','pbkdf2_sha256$150000$Pmvk0Cxwpnr5$Mm4nr0VNwtAF89lMFUjYufD8DYmXza76pAoRT1BSlTg=',4,2),('2020-06-30 11:58:07.422000',8,'hil_test','pbkdf2_sha256$150000$QIKAkXLNnr88$kavWfzfc/7TMmH97hXBrfwNwQ+iQooQ4DYpkbU10RIE=',6,2),('2019-08-19 07:44:06.839000',9,'hvh_test','pbkdf2_sha256$150000$oKigAA5zpZfa$75EMGXFfqtUtrb2d4Nud0e7B1hJo9PuwfnPzqiGMnXM=',5,2),(NULL,10,'frb_test','pbkdf2_sha256$150000$HhdWVw02QCZJ$PP3aKUgOe55S+5ikVm5x5YBkLt9HQqh/j70+kcwdxxk=',7,2),(NULL,11,'bis_test','pbkdf2_sha256$150000$zoh8wFL9OP1s$wvp1W19usdqCAIrv4Oh5vVACFKE4qKXqT7PKDvlb0ec=',8,2);
/*!40000 ALTER TABLE `main_page_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `main_page_usergroup`
--

DROP TABLE IF EXISTS `main_page_usergroup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `main_page_usergroup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_page_usergroup`
--

LOCK TABLES `main_page_usergroup` WRITE;
/*!40000 ALTER TABLE `main_page_usergroup` DISABLE KEYS */;
INSERT INTO `main_page_usergroup` VALUES (1,'admin'),(2,'user');
/*!40000 ALTER TABLE `main_page_usergroup` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2020-07-03  9:34:54
