import csv
import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Candle
from .serializers import CandleSerializer
from datetime import datetime as dt, timedelta
import datetime
from django.shortcuts import render

import io

def index(request):
    return render(request, 'index.html')


@api_view(['POST'])
@csrf_exempt
def process_csv(request):
    # Get CSV file and timeframe from request
    csv_file = request.FILES['csv_file']
    timeframe = int(request.data.get('timeframe', 1))

    # Read CSV and process data
    candles = []
    with io.TextIOWrapper(csv_file, encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            candle = Candle(
                open=Decimal(row['OPEN']),
                high=Decimal(row['HIGH']),
                low=Decimal(row['LOW']),
                close=Decimal(row['CLOSE']),
                date=dt.strptime(row['DATE'] + ' ' + row['TIME'], '%Y%m%d %H:%M')

            )
            candles.append(candle)

    # Convert to given timeframe
    converted_candles = convert_to_timeframe(candles, timeframe)
    

    # Serialize and store data in JSON file
    serializer = CandleSerializer(candles, many=True)
    json_data = serializer.data
    json_file_path = 'converted_data.json'
    with open(json_file_path, 'w') as json_file:
        json.dump(json_data, json_file)

    # Return JSON response with download link
    response_data = {'message': 'Data processed successfully', 'download_link': json_file_path}
    return JsonResponse(response_data)


def convert_to_timeframe(candles, timeframe):
    # Group candles into intervals based on the specified timeframe
    grouped_candles = []
    current_interval = None

    for candle in candles:
        if current_interval is None:
            current_interval = {
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'date': candle.date,
            }
        else:
            current_interval['high'] = max(current_interval['high'], candle.high)
            current_interval['low'] = min(current_interval['low'], candle.low)
            current_interval['close'] = candle.close

        # Check if the current candle belongs to the next interval
        current_date = candle.date
        next_interval_date = current_interval['date'] + timedelta(minutes=timeframe)

        if current_date > next_interval_date:
            grouped_candles.append(current_interval)
            current_interval = None

    return grouped_candles