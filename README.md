# 🤖 Agentic Store

**A Next-Generation Electronics Retail Agent with Blockchain Payment Integration**

Agentic Store is an intelligent AI-powered electronics retailer that combines traditional e-commerce with modern blockchain payment capabilities. Built on the A2A (Agent-to-Agent) framework, it offers personalized shopping experiences with persistent memory and secure USDC cryptocurrency payments.

## 🌟 Features

### 🛍️ **Smart Inventory Management**
- Real-time inventory checking and product search
- Comprehensive electronics catalog with pricing and stock levels
- Intelligent product recommendations based on customer queries

### 💳 **Blockchain Payment Integration**
- **USDC-only payments** across multiple networks
- **Multi-chain support**: Ethereum, Polygon, and Arbitrum
- **Real-time transaction verification** on-chain
- **Secure wallet integration** with network-specific addresses

### 🧠 **Persistent Memory & Personalization**
- **Cross-session memory** - remembers you between conversations
- **Customer preferences** - saves your shopping habits and preferences
- **Conversation history** - maintains context across multiple interactions
- **Personalized recommendations** based on past interactions

### 🔗 **Supported Networks**

| Network | Chain ID | Fees | Confirmation Time | Recommended |
|---------|----------|------|-------------------|-------------|
| **Polygon** | 137 | Low | 2-5 minutes | ✅ **Best Choice** |
| **Arbitrum** | 42161 | Very Low | 1-2 minutes | 🚀 **Fastest** |
| **Ethereum** | 1 | High | 15 minutes | 🔒 **Most Secure** |

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js (for Web3 integration)
- A blockchain wallet with USDC

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/garantor/RetailerA2A.git
   cd RetailerA2A
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your wallet address
   ```

4. **Run the agent**
   ```bash
   python src/__main__.py
   ```

5. **Start shopping**
   ```bash
   python BuyerClient.py
   ```

## 💬 Example Interactions

### Basic Shopping
```
You: What products do you have?
Agent: 📦 Current Inventory:
• Wireless Bluetooth Headphones - $79.99 (Stock: 25)
• Smartphone Case (iPhone) - $24.99 (Stock: 50)
• USB-C Charging Cable - $12.99 (Stock: 100)
...
```

### Payment Process
```
You: How can I pay for items?
Agent: 🌐 Supported Payment Networks:
Polygon (polygon) - Low fees, 2-5 minutes
Arbitrum (arbitrum) - Very low fees, 1-2 minutes
...

You: I want to pay with USDC on Polygon
Agent: 💳 Payment Information - Polygon
📍 Wallet Address: 0x742e4c5b8f8de8a3d51b4e4a8d2f6e9c1a3b5d7e
📄 USDC Contract: 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
...
```

### Payment Verification
```
You: Please verify my payment: 0x1234567890abcdef...
Agent: ✅ Payment Verified!
• Transaction: 0x1234567890abcdef...
• Amount: $79.99 USDC
• Status: Confirmed
Thank you for your payment!
```

## 🛠️ Available Commands

### Inventory Management
- `check inventory` - View all available products
- `search for [product]` - Find specific items
- `show me headphones` - Search by category

### Payment Operations
- `payment info` - Get supported networks
- `payment info polygon` - Get Polygon wallet address
- `verify payment [tx_hash] [amount] [network]` - Verify transaction

### Session Management
- `session info` - View current session details
- `new session` - Start fresh conversation
- `what did we discuss before?` - Recall conversation history

## 🏗️ Architecture

```
├── src/
│   ├── agent.py              # Core agent logic and tools
│   ├── agent_executor.py     # A2A execution framework
│   └── __main__.py          # Server entry point
├── BuyerClient.py           # Customer client interface
├── conversation_memory.json # Persistent memory storage
└── user_session.json       # Session management
```

## 🔧 Configuration

### Environment Variables
```env
AGENT_RETAILER_ONCHAIN_WALLET=0x742e4c5b8f8de8a3d51b4e4a8d2f6e9c1a3b5d7e
```

### Payment Networks
Configure supported networks in `PAYMENT_CONFIG`:
```python
PAYMENT_CONFIG = {
    "supported_networks": {
        "polygon": {
            "wallet_address": "0x...",
            "usdc_contract": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
        }
    }
}
```

## 🔒 Security Features

- **Address Verification**: Double-check wallet addresses before sending
- **Transaction Validation**: On-chain verification of payments
- **Network Confirmation**: Ensure correct blockchain network
- **Amount Verification**: Confirm exact payment amounts
- **Timeout Protection**: Payment windows with expiration

## 🎯 Use Cases

### For Customers
- **Secure Shopping**: Pay with cryptocurrency for enhanced privacy
- **Global Access**: Shop from anywhere with blockchain payments
- **Personalized Experience**: Agent remembers your preferences
- **Quick Payments**: Fast confirmations on Layer 2 networks

### For Retailers
- **Crypto Integration**: Accept USDC without traditional payment processors
- **Lower Fees**: Reduce payment processing costs
- **Global Reach**: Accept payments from customers worldwide
- **Automated Verification**: Automatic payment confirmation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support
- **Documentation**: Check our [Wiki](https://github.com/garantor/RetailerA2A/wiki)
- **Issues**: Report bugs on [GitHub Issues](https://github.com/garantor/RetailerA2A/issues)
- **Discord**: Join our [Community Discord](https://discord.gg/agentic-store)

## 🚀 Roadmap

- [ ] **Multi-token Support** - Add support for other cryptocurrencies
- [ ] **Order Management** - Advanced order tracking and history
- [ ] **Loyalty Program** - Blockchain-based rewards system
- [ ] **Mobile App** - React Native mobile client
- [ ] **Merchant Dashboard** - Web interface for inventory management
- [ ] **Smart Contracts** - Escrow and automated fulfillment

---

**Built with ❤️ using A2A Framework and Web3 Technologies**

*Experience the future of retail with Agentic Store - Where AI meets Blockchain*



NOTE - README Generated by AI