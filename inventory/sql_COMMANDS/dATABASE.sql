/*Database Commands*/
create database Inventory_Details;
use Inventory_Details;
SELECT @@SERVERNAME;
EXEC xp_readerrorlog 0,1, N'Server is listening on';

/*List of Select Statements*/
select name from sys.tables;
select * from dbo.inventoryapp_request;
select * from inventoryapp_equipment;
Select * from inventoryapp_labequipment;
Select * from inventoryapp_lab;
select*from inventoryapp_equipment;
Select * from inventoryapp_adminlog;
select * from inventoryapp_access;
select * from inventoryapp_Section;
select * from inventoryapp_customuser;
/*list of Delete Comamands*/
delete from inventoryapp_adminlog;
dbcc checkident('dbo.inventoryapp_adminlog',reseed, 0000);
delete from inventoryapp_lab;
dbcc checkident('dbo.inventoryapp_lab',reseed,000);
delete from inventoryapp_equipment;
delete from inventoryapp_labequipment;
DBCC CHECKIDENT ('dbo.inventoryapp_labequipment', RESEED, 1000);
DBCC CHECKIDENT ('dbo.inventoryapp_equipment', RESEED, 1000);
DBCC CHECKIDENT ('Inventoryapp_access', RESEED, 000);
delete from inventoryapp_customuser;
delete from inventoryapp_access ;
DBCC CHECKIDENT ('dbo.Inventoryapp_CustomUser',RESEED,00000);
delete from inventoryapp_access;
DBCC CHECKIDENT('dbo.inventoryapp_access',RESEED,000);

/*Update commands*/
Update dbo.inventoryapp_customuser set First_Name='Manu', LAst_Name='Dhiman',role='SuperUser'
where id=1;
Update dbo.inventoryapp_customuser set Role='SuperUser',is_staff=1,is_superuser=1,is_active=1 where id=1;


/*Constraint revelation*/
SELECT name, type_desc 
FROM sys.indexes 
WHERE object_id = OBJECT_ID('dbo.inventoryapp_adminlog');
SELECT COLUMN_NAME 
FROM INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE 
WHERE CONSTRAINT_NAME = 'UQ__inventor__A9D10534A0BF1397';
Select Column_Name from INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE where Constraint_name ='PK__inventor__3213E83F8AF40964';
