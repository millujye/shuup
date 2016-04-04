# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from shoop.core.fields import MoneyValueField
from shoop.core.pricing import PriceInfo

from ._services_base import ServiceBehaviorComponent
from ._methods import Carrier, PaymentMethod, PaymentProcessor, ShippingMethod


class CustomCarrier(Carrier):
    def get_service_choices(self):
        return [self.service_choice('custom', _("Custom shipping"))]

    def _create_service(self, choice_identifier, **kwargs):
        return ShippingMethod.objects.create(
            carrier=self, choice_identifier=choice_identifier, **kwargs)


class CustomPaymentProcessor(PaymentProcessor):
    def get_service_choices(self):
        return [self.service_choice('custom', _("Custom payment"))]

    def _create_service(self, choice_identifier, **kwargs):
        return PaymentMethod.objects.create(
            payment_processor=self, choice_identifier=choice_identifier, **kwargs)


class FixedCostBehaviorComponent(ServiceBehaviorComponent):
    price_value = MoneyValueField()

    def get_costs(self, service, source):
        price = source.create_price(self.price_value)
        yield (None, PriceInfo(price, price, 1), None)


class WeightLimitsBehaviorComponent(ServiceBehaviorComponent):
    min_weight = models.DecimalField(
        max_digits=36, decimal_places=6, blank=True, null=True,
        verbose_name=_("minimum weight"))
    max_weight = models.DecimalField(
        max_digits=36, decimal_places=6, blank=True, null=True,
        verbose_name=_("maximum weight"))

    def get_unavailability_reasons(self, service, source):
        weight = sum(((x.get("weight") or 0) for x in source.get_lines()), 0)
        if self.min_weight:
            if weight < self.min_weight:
                yield ValidationError(_("Minimum weight not met."), code="min_weight")
        if self.max_weight:
            if weight > self.max_weight:
                yield ValidationError(_("Maximum weight exceeded."), code="max_weight")