-- 添加分配次数字段到订单表
USE `bnsj`;

ALTER TABLE `orders` 
ADD COLUMN `assignment_count` INT DEFAULT 0 COMMENT '分配次数' AFTER `status`;

-- 更新现有订单的分配次数（根据order_assignments表统计）
UPDATE `orders` o
SET o.`assignment_count` = (
    SELECT COUNT(*) 
    FROM `order_assignments` oa 
    WHERE oa.`order_id` = o.`id`
);

