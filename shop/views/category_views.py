from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shop.models import Category, Product
from shop.serializers import CategoryCreateSerializer, CategoryResponseSerializer


def _build_category_response(category, products_qs, all_categories):
    subs = [c for c in all_categories if c.parent_category_id == category.id]
    return {
        "id": str(category.id),
        "name": category.name,
        "parent_category_id": str(category.parent_category_id) if category.parent_category_id else None,
        "parent_category_name": (
            category.parent_category.name if category.parent_category_id and category.parent_category else None
        ),
        "description": category.description,
        "profit_margin_target": category.profit_margin_target,
        "created_at": category.created_at,
        "product_count": sum(1 for p in products_qs if p.category_id == category.id),
        "sub_categories": [
            {
                "id": str(sc.id),
                "name": sc.name,
                "parent_category_id": str(sc.parent_category_id) if sc.parent_category_id else None,
                "description": sc.description,
                "profit_margin_target": sc.profit_margin_target,
                "created_at": sc.created_at,
                "product_count": sum(1 for p in products_qs if p.category_id == sc.id),
            }
            for sc in subs
        ],
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_categories(request):
    company_id = request.user.company_id
    categories = list(
        Category.objects.filter(company_id=company_id)
        .select_related("parent_category")
    )
    products = list(Product.objects.filter(company_id=company_id, is_active=True).only("category_id"))

    data = [_build_category_response(c, products, categories) for c in categories]
    return Response(CategoryResponseSerializer(data, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_category(request, category_id):
    company_id = request.user.company_id
    category = (
        Category.objects.select_related("parent_category")
        .filter(pk=category_id, company_id=company_id)
        .first()
    )
    if not category:
        return Response(status=status.HTTP_404_NOT_FOUND)

    products = list(Product.objects.filter(company_id=company_id, is_active=True).only("category_id"))
    sub_categories = list(Category.objects.filter(parent_category_id=category_id, company_id=company_id))

    data = {
        "id": str(category.id),
        "name": category.name,
        "parent_category_id": str(category.parent_category_id) if category.parent_category_id else None,
        "parent_category_name": category.parent_category.name if category.parent_category else None,
        "description": category.description,
        "profit_margin_target": category.profit_margin_target,
        "created_at": category.created_at,
        "product_count": sum(1 for p in products if p.category_id == category.id),
        "sub_categories": [
            {
                "id": str(sc.id),
                "name": sc.name,
                "parent_category_id": str(sc.parent_category_id) if sc.parent_category_id else None,
                "description": sc.description,
                "profit_margin_target": sc.profit_margin_target,
                "created_at": sc.created_at,
                "product_count": sum(1 for p in products if p.category_id == sc.id),
            }
            for sc in sub_categories
        ],
    }
    return Response(CategoryResponseSerializer(data).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_category(request):
    user = request.user
    company_id = user.company_id
    if not company_id:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    serializer = CategoryCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    parent_id = data.get("parent_category_id")
    if parent_id:
        parent = Category.objects.filter(pk=parent_id, company_id=company_id).first()
        if not parent:
            return Response({"message": "Invalid parent category."}, status=status.HTTP_400_BAD_REQUEST)

    category = Category.objects.create(
        name=data["name"],
        parent_category_id=parent_id if parent_id else None,
        description=data.get("description"),
        profit_margin_target=data.get("profit_margin_target"),
        created_by=user,
        company_id=company_id,
    )

    resp = {
        "id": str(category.id),
        "name": category.name,
        "parent_category_id": str(category.parent_category_id) if category.parent_category_id else None,
        "parent_category_name": None,
        "description": category.description,
        "profit_margin_target": category.profit_margin_target,
        "created_at": category.created_at,
        "product_count": 0,
        "sub_categories": [],
    }
    return Response(CategoryResponseSerializer(resp).data, status=status.HTTP_201_CREATED)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_category(request, category_id):
    company_id = request.user.company_id
    category = Category.objects.filter(pk=category_id, company_id=company_id).first()
    if not category:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = CategoryCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    parent_id = data.get("parent_category_id")
    if parent_id:
        if parent_id == category_id:
            return Response(
                {"message": "Category cannot be its own parent."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        parent = Category.objects.filter(pk=parent_id, company_id=company_id).first()
        if not parent:
            return Response({"message": "Invalid parent category."}, status=status.HTTP_400_BAD_REQUEST)

        # Circular reference check
        current = parent
        while current:
            if current.parent_category_id == category_id:
                return Response(
                    {"message": "Circular reference detected."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not current.parent_category_id:
                break
            current = Category.objects.filter(pk=current.parent_category_id).first()

    category.name = data["name"]
    category.parent_category_id = parent_id if parent_id else None
    category.description = data.get("description")
    category.profit_margin_target = data.get("profit_margin_target")
    category.save()

    products = list(Product.objects.filter(company_id=company_id, is_active=True).only("category_id"))
    resp = {
        "id": str(category.id),
        "name": category.name,
        "parent_category_id": str(category.parent_category_id) if category.parent_category_id else None,
        "parent_category_name": None,
        "description": category.description,
        "profit_margin_target": category.profit_margin_target,
        "created_at": category.created_at,
        "product_count": sum(1 for p in products if p.category_id == category.id),
        "sub_categories": [],
    }
    return Response(CategoryResponseSerializer(resp).data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_category(request, category_id):
    company_id = request.user.company_id
    category = Category.objects.filter(pk=category_id, company_id=company_id).first()
    if not category:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if Product.objects.filter(category_id=category_id, is_active=True).exists():
        return Response(
            {"message": "Cannot delete category with existing products."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if Category.objects.filter(parent_category_id=category_id).exists():
        return Response(
            {"message": "Cannot delete category with subcategories."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    category.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
