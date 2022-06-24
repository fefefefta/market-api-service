from rest_framework import serializers

from .models import Offer, Category


class OfferSerializer(serializers.ModelSerializer):
    parent_id = serializers.CharField(max_length=36, allow_null=True)

    class Meta:
        model = Offer
        fields = ("obj_id", "date", "name", "price", "parent_id")

    def create(self, validated_data):
        try:
            parent = Offer.objects.get(
                    obj_id=validated_data["parent_id"],
                    is_actual=True,
                )
        except Offer.DoesNotExist:
            parent = None

        try:
            actual_offer = Offer.objects.get(
                    obj_id=validated_data["obj_id"],
                    is_actual=True
                )
        except Offer.DoesNotExist:
            self.new_offers_sum = 1
            self.price_change = validated_data["price"]
            return Offer.objects.create(
                    obj_id=validated_data["obj_id"],
                    name=validated_data["name"],
                    date=validated_data["date"],
                    price=validated_data["price"],
                    parent=parent,
                    is_actual=True,
                )
        else:
            history_version = Offer.objects.get(
                    obj_id=validated_data["obj_id"],
                    is_actual=True
                )
            history_version.pk = None
            history_version.is_actual = False

            actual_offer.name = validated_data["name"]
            actual_offer.date = validated_data["date"]
            actual_offer.price = validated_data["price"]
            actual_offer.save()

            history_version.save()
            self.new_offers_sum = 0
            self.price_change = validated_data["price"]
            return actual_offer        


class CategorySerializer(serializers.ModelSerializer):
    price_change = serializers.IntegerField()
    new_offers_sum = serializers.IntegerField()
    parent_id = serializers.CharField(max_length=36, allow_null=True)
    name = serializers.CharField(allow_null=True)

    class Meta:
        model = Category
        fields = ("obj_id", "date", "name", "price_change", "new_offers_sum",
                  "parent_id")

    def create(self, validated_data):
        try:
            parent = Category.objects.get(
                    obj_id=validated_data["parent_id"],
                    is_actual=True,
                )    
        except Category.DoesNotExist:
            parent = None

        try:
            actual_category = Category.objects.filter(
                    obj_id=validated_data["obj_id"],
                    is_actual=True,
                )[0]
            # print('1')
        except IndexError:
            # print('2')
            return Category.objects.create(
                    obj_id=validated_data["obj_id"],
                    name=validated_data["name"],
                    date=validated_data["date"],
                    offers_price=validated_data["price_change"],
                    all_offers=validated_data["new_offers_sum"],
                    parent=parent,
                    is_actual=True,
                )
        else:
            # print('3')
            history_version = Category.objects.filter(
                    obj_id=validated_data["obj_id"],
                    is_actual=True,
                )[0]
            history_version.pk = None
            history_version.is_actual = False

            actual_category.name = (validated_data.get("name") 
                                    or actual_category.name)
            actual_category.date = validated_data["date"]
            actual_category.offers_price += validated_data["price_change"]
            actual_category.all_offers += validated_data["new_offers_sum"]
            actual_category.save()

            history_version.save()
            return actual_category