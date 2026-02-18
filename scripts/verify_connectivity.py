
import requests
import sys
import json

def check_rest():
    url = "http://localhost:8000/api/v1/models"
    print(f"Checking REST API: {url}")
    try:
        resp = requests.get(url)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("REST API: OK")
            return True
        else:
            print(f"REST API: FAILED ({resp.text})")
            return False
    except Exception as e:
        print(f"REST API: ERROR ({e})")
        return False

def check_graphql(port):
    url = f"http://localhost:{port}/graphql"
    print(f"Checking GraphQL API on port {port}: {url}")
    query = """
    query {
      allModels {
        nodes {
          name
        }
      }
    }
    """
    try:
        resp = requests.post(url, json={"query": query})
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"GraphQL API (Port {port}): OK")
            return True
        else:
            print(f"GraphQL API (Port {port}): FAILED ({resp.text})")
            return False
    except Exception as e:
        print(f"GraphQL API (Port {port}): ERROR ({e})")
        return False

def main():
    print("--- CONNECTIVITY DIAGNOSTIC ---")
    rest_ok = check_rest()
    gql_5000 = check_graphql(5000)
    gql_5001 = check_graphql(5001)
    
    print("\n--- SUMMARY ---")
    print(f"REST (8000): {'✅' if rest_ok else '❌'}")
    print(f"GraphQL (5000): {'✅' if gql_5000 else '❌'}")
    print(f"GraphQL (5001): {'✅' if gql_5001 else '❌'}")
    
    if not gql_5000 and gql_5001:
        print("\nDIAGNOSIS: Database is on 5001, but Frontend likely targets 5000.")

if __name__ == "__main__":
    main()
