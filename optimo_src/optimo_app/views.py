from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

import json
import datetime

@api_view(['POST'])
def statement_upload(request):
    if request.method != 'POST' or not request.FILES.get('json_file'):
        return Response({"message": "Bad request"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        statement_data = json.load(request.FILES['json_file'])
        monthwise_summary_data = statement_data['Data']['Summary']['monthwiseSummary']
        ecs_nach_return_transactions_data = statement_data['Data']["ECS,NACH,CASH Return"]["ECS/NACH RETURN TRANSACTIONS"]
        monthwise_eod_data = statement_data['Data']['Eod analysis']['EOD MONTH WISE']

        # extracting monthly netInflows
        monthly_net_inflows = [
            {'monthYear': item['monthYear'], 'netInflows': item['netInflows']}
            for item in monthwise_summary_data
        ]

        # extracting monthly netCashflows
        monthly_net_cashflows = [
            {'monthYear': item['monthYear'],'cashflow': item['netInflows'] - item['netOutflows']}
            for item in monthwise_summary_data
        ]

        # extracting ECS/NACH RETURN TRANSACTIONS
        one_year_ago = datetime.date.today() - datetime.timedelta(days=365)

        ecs_nach_return_transactions_count = 0
        for item in ecs_nach_return_transactions_data:
            if bool(item["Date"]):
                if datetime.datetime.strptime(item["Date"], "%Y-%m-%d").date() > one_year_ago:
                    ecs_nach_return_transactions_count=+1

        # extracting average balance
        total_average_eod = sum(float(item['averageEod']) for item in monthwise_eod_data)
        average_balance = total_average_eod / len(monthwise_eod_data)

        # extracting average netInflows
        total_net_inflows = sum(item['netInflows'] for item in monthwise_summary_data)
        average_net_inflows = total_net_inflows / len(monthwise_summary_data)

        # output
        output_data = {
            "Data":{
                "monthly_netInflows": monthly_net_inflows,
                "monthly_netCashFlow": monthly_net_cashflows,
                "ECS/NACH return transactions count":ecs_nach_return_transactions_count,
                "average_balance":average_balance,
                "average_netInflows": average_net_inflows,
            } 
        }

        return Response(output_data, status=status.HTTP_200_OK)

    except (json.JSONDecodeError, KeyError) as e:
        return Response({"message": f"Invalid JSON format: {e}"}, status=status.HTTP_400_BAD_REQUEST)

