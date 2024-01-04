import logging
# from logging.handlers import RotatingFileHandler
import json
import hashlib

logger = logging.getLogger(__name__)

def orderbook_average_price(orderbook_data, amount, isSell):
    # Créez une copie triée de l'ordre
    amount = round(amount, 6)
    sorted_orderbook_data = {
        'b': sorted(orderbook_data['b'], key=lambda x: float(x[0]), reverse=True),
        'a': sorted(orderbook_data['a'], key=lambda x: float(x[0]))
    }  


    # firstValue = orderbook_data['b'][0][0]

    # # Convertir le dictionnaire en chaîne JSON
    # json_data = json.dumps(sorted_orderbook_data, sort_keys=True)
    # # Utiliser hashlib pour obtenir un hash stable
    # hash_value = hashlib.sha256(json_data.encode()).hexdigest()

    # # Convertir le dictionnaire en chaîne JSON
    # json_data_not_sorted = json.dumps(orderbook_data, sort_keys=True)
    # # Utiliser hashlib pour obtenir un hash stable
    # hash_value_not_sorted = hashlib.sha256(json_data_not_sorted.encode()).hexdigest()
    # logging.info(f'First value {firstValue} - Unsorted orderbook hash : {hash_value_not_sorted} - Sorted orderbook hash_value : {hash_value}')

    ask_or_bid = 'b' if isSell else 'a'

    # Assurez-vous que les données de l'ordre sont disponibles
    if ask_or_bid not in sorted_orderbook_data or not sorted_orderbook_data[ask_or_bid]:
        return None  # Aucune donnée d'ordre disponible

    bids = sorted_orderbook_data[ask_or_bid]  # Liste des enchères

    total_price = 0.0
    total_amount = 0.0

    # Parcourez les enchères jusqu'à ce que vous ayez suffisamment d'amount
    for bid in bids:
        price, bid_amount = map(float, bid)  # Convertissez les valeurs en float
        if total_amount + bid_amount >= amount:
            # Si le montant total dépasse ou atteint le montant souhaité, arrêtez
            remaining_amount = amount - total_amount
            total_price += price * remaining_amount
            total_amount += remaining_amount
            break
        else:
            # Sinon, continuez à accumuler le montant
            total_price += price * bid_amount
            total_amount += bid_amount

    # Calcul du prix moyen
    if total_amount > 0:
        average_price = total_price / total_amount
        return average_price
    else:
        return orderbook_average_price(orderbook_data, 1, isSell)# Aucun montant disponible dans l'orderbook pour le montant donné


# # Exemple d'utilisation
# orderbook_data = {
#     's': 'BTCUSDC',
#     'b': [['34930', '0.02'], ['34928.9', '0.4'], ['34928', '0.058322'], ['34927.18', '0.0859']],
#     'a': [['34949.54', '0.05'],['34951.11', '1']],
#     # ...
# }

def orderbook_after_opportunity(orderbook, amount, isSell):
    """
    Calcule le prix moyen d'un asset dans l'orderbook après l'exécution d'un montant donné.

    :param orderbook: Données de l'orderbook sous forme de dictionnaire avec clés 'b' (bid) et 'a' (ask).
    :param amount: Montant pour lequel calculer le prix moyen.
    :param isSell: Booléen indiquant si l'actif à vendre est BTC.
    :return: Tuple contenant le prix moyen et l'orderbook mis à jour.
    """
    # Créer une copie triée de l'orderbook pour éviter de modifier l'original
    sorted_orderbook = {
        'b': sorted(orderbook['b'], key=lambda x: float(x[0]), reverse=True),
        'a': sorted(orderbook['a'], key=lambda x: float(x[0]))
    }

    ask_or_bid = 'b' if isSell else 'a'

    # S'assurer que les données de l'ordre sont disponibles
    if ask_or_bid not in sorted_orderbook or not sorted_orderbook[ask_or_bid]:
        return None, orderbook  # Retourner None et l'orderbook original si aucune donnée n'est disponible

    total_price = 0.0
    total_amount = 0.0
    orders = sorted_orderbook[ask_or_bid]  # Liste des ordres
    remaining_amount = amount  # Montant restant à traiter

    # Parcourir les ordres pour calculer le prix moyen
    for i in range(len(orders)):
        price, order_amount = map(float, orders[i])  # Convertir les valeurs en float
        order_volume = min(order_amount, remaining_amount)
        total_price += price * order_volume
        total_amount += order_volume
        remaining_amount -= order_volume

        # Mise à jour de la quantité de l'ordre actuel
        orders[i][1] = str(order_amount - order_volume)

        if remaining_amount <= 0:
            break  # Quitter la boucle si le montant a été entièrement traité

    # Filtrer les ordres complètement utilisés
    sorted_orderbook[ask_or_bid] = [order for order in orders if float(order[1]) > 0]

    # Calcul du prix moyen
    average_price = total_price / total_amount if total_amount > 0 else 0

    return sorted_orderbook


# # Exemple d'utilisation :
# orderbook = {
#     'b': [['10000', '4'], ['5000', '5'], ['10', '10']],
#     'a': [['10001', '5'], ['5000', '2'], ['10', '10']]
# }
# amounts = 15
# isSell = False  # Supposons que nous vendons BTC

# new_orderbook = orderbook_after_opportunity(orderbook, amounts, isSell)
# print(new_orderbook)
