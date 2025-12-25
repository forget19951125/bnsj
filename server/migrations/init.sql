-- 创建数据库
CREATE DATABASE IF NOT EXISTS `bn_auto` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `bn_auto`;

-- 用户表
CREATE TABLE IF NOT EXISTS `users` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    `password` VARCHAR(255) NOT NULL COMMENT '密码（加密）',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1-正常，2-已过期，3-已禁用',
    `expire_at` DATETIME COMMENT '账号过期时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_username` (`username`),
    INDEX `idx_status` (`status`),
    INDEX `idx_expire_at` (`expire_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 订单表
CREATE TABLE IF NOT EXISTS `orders` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '订单ID',
    `time_increments` VARCHAR(50) NOT NULL COMMENT '时间增量，如TEN_MINUTE',
    `symbol_name` VARCHAR(20) NOT NULL COMMENT '交易对，如BTCUSDT',
    `direction` VARCHAR(10) NOT NULL COMMENT '方向：LONG或SHORT',
    `valid_duration` INT NOT NULL COMMENT '有效时间（秒）',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1-待分配，2-已分配，3-已过期',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_status` (`status`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';

-- 订单分配记录表
CREATE TABLE IF NOT EXISTS `order_assignments` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
    `order_id` BIGINT NOT NULL COMMENT '订单ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `assigned_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '分配时间',
    `executed_at` DATETIME COMMENT '执行时间',
    `execution_result` TEXT COMMENT '执行结果（JSON）',
    FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `uk_order_user` (`order_id`, `user_id`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_assigned_at` (`assigned_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单分配记录表';

