

-- 创建数据库 parser_component,用于存储与爬虫相关的组件
CREATE DATABASE IF NOT EXISTS parser_component;
-- 授权给用户 investor1 所有权限
GRANT ALL PRIVILEGES ON parser_component.* TO 'investor1'@'%' WITH GRANT OPTION;
# 刷新权限 权限更新后刷新才会起作用
FLUSH PRIVILEGES;




/* --------- user：investor1 ------ */
/* --------- db：parser_component ------ */
/*创建一个表，IP_availability，用于记录ip的可用性 */


CREATE TABLE IF NOT EXISTS `IP_availability`(
	`ip_address` VARCHAR(21) NOT NULL COMMENT '主键，ip的地址+端口号，最长可达21位，作为主键可确保数据库中的ip地址不会重复',
	`is_anonymous` BOOLEAN NOT NULL COMMENT '是否为高匿名，是为1，否为0',
	`is_available` BOOLEAN NOT NULL COMMENT '是否仍然可用，是为1，否为0',
	`type` VARCHAR(21) COMMENT 'IP类型，HTTP,HTTPS, (HTTP,HTTPS)',
	`submission_date` DATE NOT NULL COMMENT '提交的日期',
	PRIMARY KEY ( `ip_address` )
) ENGINE=InnoDB DEFAULT CHARSET=utf8 
COMMENT '记录IP的可用性';






/* --------- user：investor1 ------ */
/* --------- db：parser_component ------ */
/*创建一个表，fake_user_agent，用于存储生成的假UA（用户代理）*/

CREATE TABLE IF NOT EXISTS `fake_user_agent`(
	`id` MEDIUMINT NOT NULL AUTO_INCREMENT,
	`ua` VARCHAR(1000) NOT NULL COMMENT '用户代理',
	`submission_date` DATE NOT NULL COMMENT '提交的日期',
	PRIMARY KEY ( `id` )
) ENGINE=InnoDB DEFAULT CHARSET=utf8 
COMMENT '生成的假UA（用户代理）';















-- 创建数据库 target_pool,用作标的池，存储标的物，对应交易策略
CREATE DATABASE IF NOT EXISTS target_pool;
-- 授权给用户 investor1 所有权限
GRANT ALL PRIVILEGES ON target_pool.* TO 'investor1'@'%' WITH GRANT OPTION;
# 刷新权限 权限更新后刷新才会起作用
FLUSH PRIVILEGES;



/* --------- user：investor1 ------ */
/* --------- db：target_pool ------ */
/*创建一个表，fund_target，用于存储基金标的,对应策略*/

CREATE TABLE IF NOT EXISTS `fund_target`(
	`fund_code` VARCHAR(12) NOT NULL COMMENT '基金代码',
	`fund_name` VARCHAR(50) NOT NULL COMMENT '基金名称',
	`fund_type`  VARCHAR(12) NOT NULL COMMENT '基金类型，指数，混合，股票，债券型，联接，，，',
	`tracking_index`  VARCHAR(50) COMMENT '跟踪指数名称',
	`tracking_index_code`  VARCHAR(12) COMMENT '跟踪指数代码',
	`hold_or_not`  tinyint(1) COMMENT '当前是否持有,1为持有，0不持有',
	`valuation_method` COMMENT '估值方法',
	`B&H_strategy`  COMMENT '买入持有策略',
	`sell_out_strategy`  COMMENT '卖出策略',
	`monitoring_frequency`  COMMENT '监控频率',
	`submission_date` DATE NOT NULL COMMENT '提交的日期',
	PRIMARY KEY ( `fund_code` )
) ENGINE=InnoDB DEFAULT CHARSET=utf8 
COMMENT '基金标的池';