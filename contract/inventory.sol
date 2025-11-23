// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Import Ownable from OpenZeppelin (Remix can fetch from GitHub)
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v4.8.0/contracts/access/Ownable.sol";

contract Inventory is Ownable {
    struct Product {
        uint256 productId;
        uint256 quantity;
        uint256 lastUpdated;
        bool discountApplied;
    }

    mapping(uint256 => Product) public products;
    event StockAdded(uint256 indexed productId, uint256 quantity, uint256 timestamp);
    event Restocked(uint256 indexed productId, uint256 quantity, uint256 timestamp);
    event DiscountApplied(uint256 indexed productId, uint256 discountPercent, uint256 timestamp);

    // Add or update a product quantity (owner only)
    function addOrUpdateProduct(uint256 _productId, uint256 _quantity) public onlyOwner {
        products[_productId] = Product(_productId, _quantity, block.timestamp, products[_productId].discountApplied);
        emit StockAdded(_productId, _quantity, block.timestamp);
    }

    // Restock (increase) quantity
    function restock(uint256 _productId, uint256 _quantity) public onlyOwner {
        Product storage p = products[_productId];
        p.quantity += _quantity;
        p.lastUpdated = block.timestamp;
        emit Restocked(_productId, _quantity, block.timestamp);
    }

    // Apply discount flag (does not store discount value to keep minimal)
    function applyDiscount(uint256 _productId) public onlyOwner {
        Product storage p = products[_productId];
        p.discountApplied = true;
        p.lastUpdated = block.timestamp;
        emit DiscountApplied(_productId, 0, block.timestamp); // 0 placeholder percent (backend handles percent)
    }

    // Minimal getter (public mapping already gives products)
}
