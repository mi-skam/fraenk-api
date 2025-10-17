# Fraenk API Documentation

## Base URL
```
https://app.fraenk.de/fraenk-rest-service/app/v13
```

## Authentication

### Headers
All requests require these base headers:
```json
{
  "X-Tenant": "fraenk",
  "X-App-OS": "Android",
  "X-App-Device": "Python-Client",
  "X-App-Device-Vendor": "Python",
  "X-App-OS-Version": "13",
  "X-App-Version": "1.13.9"
}
```

Authenticated requests also include:
```json
{
  "Authorization": "Bearer {access_token}"
}
```

### Login Flow (MFA)

#### Step 1: Initiate Login
**POST** `/login`

**Headers:**
- `Content-Type: application/x-www-form-urlencoded`

**Request Body:**
```
grant_type=password
username={email}
password={password}
scope=app
```

**Response (HTTP 401):**
```json
{
  "error": "mfa_required",
  "error_description": "Wir schicken dir einen 6-stelligen Bestätigungscode per SMS an deine Rufnummer mit den Endziffern *********521",
  "mfa_token": "eyJraWQi..."
}
```

#### Step 2: Complete Login with MFA
**POST** `/login-with-mfa`

**Headers:**
- `Content-Type: application/x-www-form-urlencoded`

**Request Body:**
```
username={email}
password={password}
mtan={sms_code}
mfa_token={mfa_token_from_step_1}
```

**Response (HTTP 200):**
```json
{
  "access_token": "eyJraWQi...",
  "refresh_token": "eyJraWQi...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**JWT Token Payload:**
```json
{
  "sub": "f:128120da-8e28-4856-af5d-75bc9a6654d1:7555659511",
  "aud": "app",
  "iss": "congstar",
  "exp": 1760689639,
  "iat": 1760686039
}
```

**Note:** The `sub` field contains the customer ID in format `f:{uuid}:{numeric_customer_id}`. Extract the last part (numeric ID) for API calls.

---

## Contracts

### Get Contracts
**GET** `/customers/{customer_id}/contracts`

**Headers:**
- `Authorization: Bearer {access_token}`

**Response:**
```json
[
  {
    "id": "contract_id_here",
    "status": "ACTIVE",
    ...
  }
]
```

---

## Data Consumption

### Get Data Consumption
**GET** `/customers/{customer_id}/contracts/{contract_id}/dataconsumption`

**Headers:**
- `Authorization: Bearer {access_token}`
- `Cache-Control: no-cache` (optional, to bypass cache)

**Response:**
```json
{
  "customer": {
    "msisdn": "0151 - 29489521",
    "contractType": "POST_PAID"
  },
  "passes": [
    {
      "passName": "Vertragsvolumen",
      "type": "INCLUSIVE",
      "usedVolume": "5,17 GB",
      "usedBytes": 5560651713,
      "initialVolume": "25 GB",
      "initialVolumeBytes": 26843545600,
      "expectedConsumption": "49,29 GB",
      "percentageConsumption": 21,
      "expiryTimestamp": 1761951599000,
      "lastUpdateTimestamp": 1760681799000,
      "speedon": false,
      "speedStepDown": false,
      "messagingOption": false,
      "steps": []
    }
  ],
  "bookableDataPassesAvailable": true
}
```

## Data Models

### DataConsumptionResponse
| Field | Type | Description |
|-------|------|-------------|
| `customer` | `Customer` | Customer information |
| `passes` | `Array<DataPass>` | List of data passes |
| `bookableDataPassesAvailable` | `boolean` | Whether additional passes can be booked |

### Customer
| Field | Type | Description |
|-------|------|-------------|
| `msisdn` | `string` | Phone number (formatted) |
| `contractType` | `string` | Contract type (e.g., "POST_PAID") |

### DataPass
| Field | Type | Description |
|-------|------|-------------|
| `passName` | `string` | Name of the data pass |
| `type` | `string` | Pass type (e.g., "INCLUSIVE") |
| `usedVolume` | `string` | Used data volume (human-readable) |
| `usedBytes` | `number` | Used data volume in bytes |
| `initialVolume` | `string` | Initial data volume (human-readable) |
| `initialVolumeBytes` | `number` | Initial data volume in bytes |
| `expectedConsumption` | `string` | Expected consumption (human-readable) |
| `percentageConsumption` | `number` | Percentage of data used (0-100) |
| `expiryTimestamp` | `number` | Unix timestamp (milliseconds) when pass expires |
| `lastUpdateTimestamp` | `number` | Unix timestamp (milliseconds) of last update |
| `speedon` | `boolean` | Whether speed-on is active |
| `speedStepDown` | `boolean` | Whether speed step-down is active |
| `messagingOption` | `boolean` | Whether messaging option is enabled |
| `steps` | `Array<any>` | Additional steps/tiers (if any) |

---

## Error Handling

### Common Error Response Format
```json
{
  "errorCode": "123",
  "errorReason": "error_identifier",
  "errorText": "Human-readable error message in German"
}
```

### HTTP Status Codes
- `200`: Success
- `401`: Authentication required / Invalid credentials / MFA required
- `404`: Resource not found
- `400`: Bad request

---

## Notes

1. **MFA is Required**: Every login requires SMS verification
2. **Customer ID Format**: Extract the numeric part from JWT `sub` field
3. **Timestamps**: All timestamps are in milliseconds (Unix epoch * 1000)
4. **Data Volumes**: API returns both human-readable strings and byte values
5. **Cache Control**: Use `Cache-Control: no-cache` header to get real-time data
