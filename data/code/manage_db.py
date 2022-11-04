import argparse
import os

import boto3
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


def create_table(db, table_name):
    db.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "Type", "KeyType": "HASH"},
            {"AttributeName": "Id", "KeyType": "RANGE"},
        ],
        LocalSecondaryIndexes=[
            {
                "IndexName": "TokenIndex",
                "KeySchema": [
                    {"AttributeName": "Type", "KeyType": "HASH"},
                    {"AttributeName": "Token", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "TokenKanaIndex",
                "KeySchema": [
                    {"AttributeName": "Type", "KeyType": "HASH"},
                    {"AttributeName": "TokenKana", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "DictionaryFormIndex",
                "KeySchema": [
                    {"AttributeName": "Type", "KeyType": "HASH"},
                    {"AttributeName": "DictionaryForm", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "DictionaryFormKanaIndex",
                "KeySchema": [
                    {"AttributeName": "Type", "KeyType": "HASH"},
                    {"AttributeName": "DictionaryFormKana", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        AttributeDefinitions=[
            {"AttributeName": "Type", "AttributeType": "S"},
            {"AttributeName": "Id", "AttributeType": "S"},
            {"AttributeName": "Token", "AttributeType": "S"},
            {"AttributeName": "TokenKana", "AttributeType": "S"},
            {"AttributeName": "DictionaryForm", "AttributeType": "S"},
            {"AttributeName": "DictionaryFormKana", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
        Tags=[
            {"Key": "service", "Value": "YuruCorpus"},
        ],
    )


def add_data(db, table_name, data_dir):
    summary = pd.read_csv(os.path.join(data_dir, "summary_processed.csv"))
    summary = summary.fillna("")
    morphemes_df = pd.read_csv(os.path.join(data_dir, "morphemes_processed.csv"))
    morphemes_df = morphemes_df.fillna("")

    table = db.Table(table_name)
    morphemes_default_columns = [
        "Type",
        "Id",
        "Speaker",
        "Token",
        "TokenKana",
        "DictionaryForm",
        "DictionaryFormKana",
    ]
    for default_column in morphemes_default_columns:
        if default_column not in morphemes_df.columns:
            morphemes_df[default_column] = np.NAN

    with table.batch_writer() as batch:
        for episode in tqdm(summary.itertuples(), total=len(summary)):
            batch.put_item(
                Item={
                    "Type": "Episode",
                    "Id": str(episode.Id),
                    "Title": episode.Title,
                    "PublicationDate": episode.PublicationDate,
                    "ThumbnailUrl": episode.ThumbnailUrl,
                    "VideoUrl": episode.VideoUrl,
                    "Channel": episode.Channel,
                    "IsAnalyzed": episode.IsAnalyzed,
                }
            )

        def write(
                morpheme_id,
                token,
                speaker,
                token_kana,
                dictionary_form,
                dictionary_form_kana,
                pbar,
        ):
            pbar.update(1)
            if morpheme_id == "1#00:00:00#0":
                return

            item = {
                "Type": "Morpheme",
                "Id": str(morpheme_id),
                "Token": str(token),
                "Speaker": str(speaker) if not pd.isna(speaker) else "",
            }
            if not pd.isna(token_kana):
                item["TokenKana"] = token_kana
            if not pd.isna(dictionary_form):
                item["DictionaryForm"] = dictionary_form
            if not pd.isna(dictionary_form_kana):
                item["DictionaryFormKana"] = dictionary_form_kana
            try:
                batch.put_item(Item=item)
            except Exception:
                print("##############################")
                print(item)

        with tqdm(total=len(morphemes_df)) as progress_bar:
            np.vectorize(write)(
                morphemes_df["Id"],
                morphemes_df["Token"],
                morphemes_df["Speaker"],
                morphemes_df["TokenKana"],
                morphemes_df["DictionaryForm"],
                morphemes_df["DictionaryFormKana"],
                progress_bar,
            )


def main():
    parser = argparse.ArgumentParser(description="Create DynamoDB table")
    parser.add_argument("table_name", help="table name")
    parser.add_argument("--remote", help="Deploy to remote", action="store_true")
    parser.add_argument("--delete", help="Delete existing table", action="store_true")
    parser.add_argument("--create", help="Create table", action="store_true")
    parser.add_argument("--data_dir", help="Add data", type=str)
    args = parser.parse_args()

    if args.remote:
        db = boto3.resource(
            "dynamodb",
            region_name="ap-northeast-1",
        )
    else:
        db = boto3.resource(
            "dynamodb",
            endpoint_url="http://dynamodb-local:8000",
            region_name="ap-northeast-1",
        )

    if args.delete:
        try:
            db.Table(args.table_name).delete()
        except Exception as e:
            print(e)

    if args.create:
        create_table(db, args.table_name)

    if args.data_dir is not None:
        add_data(db, args.table_name, args.data_dir)


if __name__ == "__main__":
    main()
