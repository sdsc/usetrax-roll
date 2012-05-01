--
-- Table structure for table `attributes`
--

DROP TABLE IF EXISTS `attributes`;
CREATE TABLE `attributes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `resource` varchar(30) DEFAULT NULL,
  `client` varchar(30) DEFAULT NULL,
  `attr` varchar(30) DEFAULT NULL,
  `timestamp` int(11) DEFAULT NULL,
  `value` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `timestamp_idx` (`timestamp`)
);
