# AWS Service Catalog

Create bucket for template(s) that is referenced in the Cloudformation.

Upload product template to S3 bucket.

Run the cloudformation stack to create the product and portfolio, this also creates the association between them.

Share the portfolio with the organisational unit

Add a User / Group / Role to the portfolio with adequate permissions to launch the product

Goto product list and select launch product from the breadcrumb menu

Give this product a name and follow the menu and select ‘Create Plan’ this will show which resources are to be changed

Select Launch

## Deploy

```
aws cloudformation deploy --template-file RoleAndPolicy.yaml --stack-name Create-Policy-Test
```

## Delete Stack (Portfolio must be unshared to delete)

```
aws cloudformation delete-stack --stack-name Create-Policy-Test
```
